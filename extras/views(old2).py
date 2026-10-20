from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import AssessmentForm, LoginForm, ProfileForm, SignUpForm
from .models import StudentProfile
from .predictor import MEANINGS, level_for_score, predict_stress, recommendations_for


def _get_profile(user):
    profile, _ = StudentProfile.objects.get_or_create(user=user, defaults={'name': user.get_username()})
    return profile


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


# ------------------------------------------------------------------ primary attributes

@login_required
def profile(request):
    student = _get_profile(request.user)
    first_time = not student.is_complete
    form = ProfileForm(request.POST or None, instance=student)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('dashboard')
    return render(request, 'core/profile.html', {'form': form, 'first_time': first_time, 'profile': student})


# ------------------------------------------------------------------ dashboard

@login_required
def dashboard(request):
    student = _get_profile(request.user)
    if not student.is_complete:
        return redirect('profile')

    latest = request.user.assessments.first()      # newest first (see Meta.ordering)
    return render(request, 'core/dashboard.html', {
        'profile': student,
        'assessment': latest,
        'stress_score': latest.stress_score if latest else None,
        'stress_level': latest.stress_level if latest else None,
    })


# ------------------------------------------------------------------ questionnaire + results

@login_required
def assessment(request):
    student = _get_profile(request.user)
    if not student.is_complete:
        return redirect('profile')

    previous = request.user.assessments.first()
    initial = {}
    if previous:   # dynamic attributes are pre-filled so the student only changes what changed
        initial = {
            'height_cm': previous.height_cm,
            'weight_kg': previous.weight_kg,
            'chronic_illnesses': previous.chronic_illnesses,
            'avg_daily_study_hours': previous.avg_daily_study_hours,
        }

    form = AssessmentForm(request.POST or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        result = form.save(commit=False)
        result.user = request.user
        result.stress_score = predict_stress(result)
        result.stress_level = level_for_score(result.stress_score)
        result.save()
        return redirect('results')
    return render(request, 'core/assessment.html', {'form': form, 'profile': student})


@login_required
def results(request):
    latest = request.user.assessments.first()
    if latest is None:
        return redirect('assessment')
    return render(request, 'core/results.html', {
        'profile': _get_profile(request.user),
        'assessment': latest,
        'stress_score': latest.stress_score,
        'stress_level': latest.stress_level,
        'meaning': MEANINGS[latest.stress_level],
        'recommendations': recommendations_for(latest, latest.stress_level),
    })
