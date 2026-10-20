from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.forms.models import model_to_dict
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import AssessmentForm, LoginForm, ProfileForm, SignUpForm
from .models import StudentProfile


def _get_profile(user):
    profile, _ = StudentProfile.objects.get_or_create(user=user, defaults={'name': user.get_username()})
    return profile


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


# ------------------------------------------------------------------ primary attributes

@login_required
def profile(request):
    student = _get_profile(request.user)
    first_time = not student.is_complete
    blocked = False

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    elif request.GET.get('required') and first_time:
        # The student tried to open another page. Validate what is saved so far,
        # so every missing field shows "This field is required."
        blocked = True
        form = ProfileForm(model_to_dict(student, fields=ProfileForm.Meta.fields), instance=student)
    else:
        form = ProfileForm(instance=student)

    return render(request, 'core/profile.html', {
        'form': form, 'first_time': first_time, 'blocked': blocked, 'profile': student,
    })


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
    })


# ------------------------------------------------------------------ questionnaire

@login_required
def assessment(request):
    student = _get_profile(request.user)
    if not student.is_complete:
        return _profile_required()

    form = AssessmentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        result = form.save(commit=False)
        result.user = request.user
        result.save()          # stress_score / stress_level stay empty until the ML model is connected
        return redirect('dashboard')
    return render(request, 'core/assessment.html', {'form': form, 'profile': student})
