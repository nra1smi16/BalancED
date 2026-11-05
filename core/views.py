import logging
from datetime import date

from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.forms.models import model_to_dict
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from .charts import build_chart
from django.shortcuts import get_object_or_404, redirect, render
from .models import Assessment, ExamDate, StudentProfile


from .forms import (
    AssessmentForm, LoginForm, ProfileForm, SignUpForm,
    StyledPasswordChangeForm, UsernameChangeForm,
)
from .models import ExamDate, StudentProfile
from .ai import allowed_for as ai_allowed_for, ask_ai, is_enabled as ai_is_enabled
from .notes import daily_note
from .predictor import level_for_score, predict_stress
from .support import COUNSELING

logger = logging.getLogger(__name__)


def _get_profile(user):
    profile, _ = StudentProfile.objects.get_or_create(user=user, defaults={'name': user.get_username()})
    return profile


def _sync_ai_choice(user, profile, was_on):
    """
    Keeps ai_opt_in_at and the saved AI notes in step with the AI choice.
    The profile object must already hold the new value; the caller saves it.
    """
    if profile.ai_opt_in and not was_on:
        profile.ai_opt_in_at = timezone.now()           # record when they agreed
    elif not profile.ai_opt_in:
        profile.ai_opt_in_at = None
        if was_on:                                       # turning it off removes the notes the AI wrote
            user.assessments.update(ai_advice='')


def _profile_required():
    """Send the student to the profile page and make it point out the missing fields."""
    return redirect(f"{reverse('profile')}?required=1")


def _render_welcome(request, login_form=None, signup_form=None, active_tab='login', status=200):
    return render(request, 'core/welcome.html', {
        'login_form': login_form or LoginForm(request, prefix='login'),
        'signup_form': signup_form or SignUpForm(prefix='signup'),
        'active_tab': active_tab,
    }, status=status)


# ------------------------------------------------------------------ welcome / auth

def welcome(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return _render_welcome(request)


@require_POST
def login_view(request):
    form = LoginForm(request, data=request.POST, prefix='login')
    if form.is_valid():
        user = form.get_user()
        login(request, user)
        return redirect('dashboard' if _get_profile(user).is_complete else 'profile')
    return _render_welcome(request, login_form=form, active_tab='login', status=400)


@require_POST
def signup_view(request):
    form = SignUpForm(request.POST, prefix='signup')
    if form.is_valid():
        user = form.save()
        login(request, user)
        return redirect('profile')          # new students fill in the primary attributes next
    return _render_welcome(request, signup_form=form, active_tab='signup', status=400)


@require_POST
def logout_view(request):
    logout(request)
    return redirect('welcome')


# ------------------------------------------------------------------ about page (open to everyone)

def about(request):
    return render(request, 'core/about.html')


# ------------------------------------------------------------------ primary attributes

@login_required
def profile(request):
    student = _get_profile(request.user)
    first_time = not student.is_complete
    blocked = False
    was_opted_in = student.ai_opt_in          # read before the form changes the object

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=student)
        if form.is_valid():
            saved = form.save(commit=False)
            _sync_ai_choice(request.user, saved, was_opted_in)
            saved.save()
            messages.success(request, 'Your profile was saved.')
            return redirect('dashboard')
    elif request.GET.get('required') and first_time:
        # The student tried to open another page. Validate what is saved so far,
        # so every missing field shows "This field is required."
        blocked = True
        form = ProfileForm(model_to_dict(student, fields=ProfileForm.Meta.fields), instance=student)
    else:
        form = ProfileForm(instance=student)

    return _render_profile(request, student, form=form, first_time=first_time, blocked=blocked)


def _render_profile(request, student, *, form, first_time=None, blocked=False,
                    username_form=None, password_form=None, status=200):
    return render(request, 'core/profile.html', {
        'form': form,
        'first_time': (not student.is_complete) if first_time is None else first_time,
        'blocked': blocked,
        'profile': student,
        'ai_available': ai_is_enabled(),
        'username_form': username_form or UsernameChangeForm(request.user, initial={'username': request.user.get_username()}),
        'password_form': password_form or StyledPasswordChangeForm(request.user),
    }, status=status)


@login_required
@require_POST
def change_username(request):
    student = _get_profile(request.user)
    form = UsernameChangeForm(request.user, request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, 'Your username was changed.')
        return redirect('profile')
    return _render_profile(request, student, form=ProfileForm(instance=student), username_form=form, status=400)


@login_required
@require_POST
def change_password(request):
    student = _get_profile(request.user)
    form = StyledPasswordChangeForm(request.user, request.POST)
    if form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)       # keeps the student logged in after the change
        messages.success(request, 'Your password was changed.')
        return redirect('profile')
    return _render_profile(request, student, form=ProfileForm(instance=student), password_form=form, status=400)


# ------------------------------------------------------------------ dashboard

@login_required
def dashboard(request):
    student = _get_profile(request.user)
    if not student.is_complete:
        return _profile_required()

    latest = request.user.assessments.first()      # newest first (see Meta.ordering)
    return render(request, 'core/dashboard.html', {
        'profile': student,
        'assessment': latest,
        'stress_score': latest.stress_score if latest else None,
        'stress_level': latest.stress_level if latest else None,
        'daily_note': daily_note(latest.stress_level if latest else None, latest,
                                 gentle=student.has_chronic_condition),
        'exam_days': [day.isoformat() for day in request.user.exam_dates.values_list('date', flat=True)],
        # the AI note is shown only to students who have it switched on
        'ai_note': latest.ai_advice if (latest and student.ai_opt_in) else '',
        'counseling': COUNSELING,
    })


@login_required
@require_POST
def toggle_exam(request):
    """Marks a calendar day as an exam day, or removes the mark if it was already there."""
    try:
        day = date.fromisoformat(request.POST.get('date', ''))
    except ValueError:
        return JsonResponse({'ok': False, 'error': 'Invalid date'}, status=400)
    if not (date(2000, 1, 1) <= day <= date(2100, 12, 31)):
        return JsonResponse({'ok': False, 'error': 'Date out of range'}, status=400)

    mark, created = ExamDate.objects.get_or_create(user=request.user, date=day)
    if not created:
        mark.delete()
    return JsonResponse({'ok': True, 'marked': created, 'date': day.isoformat()})


# ------------------------------------------------------------------ history / charts

@login_required
def history_view(request):
    student = _get_profile(request.user)
    if not student.is_complete:
        return _profile_required()

    checkins = request.user.assessments.order_by('created_at')
    chart = build_chart(checkins)
    return render(request, 'core/history.html', {
        'profile': student,
        'checkins': checkins,
        'chart': chart,
    })

#Deleting specific check ins
@login_required
@require_POST
def delete_assessment(request, pk):
    assessment = get_object_or_404(Assessment, pk=pk, user=request.user)
    assessment.delete()
    messages.success(request, 'Check-in deleted.')
    return redirect('history')


# ------------------------------------------------------------------ questionnaire

@login_required
def assessment(request):
    student = _get_profile(request.user)
    if not student.is_complete:
        return _profile_required()

    form = AssessmentForm(request.POST or None, initial={'use_ai': student.ai_opt_in})
    if request.method == 'POST' and form.is_valid():
        # The tick box on this page is the same setting as in the profile, shown again right before sending.
        use_ai = form.cleaned_data['use_ai']
        if use_ai != student.ai_opt_in:
            was_on = student.ai_opt_in
            student.ai_opt_in = use_ai
            _sync_ai_choice(request.user, student, was_on)
            student.save(update_fields=['ai_opt_in', 'ai_opt_in_at'])
            if not use_ai:
                messages.info(request, 'AI-written notes are now off, and the notes the AI wrote were removed.')
            elif ai_is_enabled():
                messages.info(request, 'AI-written notes are now on.')
            else:
                messages.info(request, 'AI-written notes are on, but they are not switched on for this site at the moment.')

        result = form.save(commit=False)
        result.user = request.user
        try:
            result.stress_score = predict_stress(student, result)
            result.stress_level = level_for_score(result.stress_score)
        except Exception:
            # The answers are still saved. The reason is written to the server log.
            logger.exception('Could not compute the stress prediction')
            messages.warning(request, 'Your answers were saved, but the stress prediction is not available right now.')
        if ai_is_enabled() and ai_allowed_for(student) and result.stress_level:
            try:
                result.ai_advice = ask_ai(student, result)      # the AI writes the Note of the Day
            except Exception:
                logger.exception('The AI request failed')       # the hand-written note is shown instead
        result.save()
        return redirect('dashboard')
    return render(request, 'core/assessment.html', {'form': form, 'profile': student, 'ai_available': ai_is_enabled()})
