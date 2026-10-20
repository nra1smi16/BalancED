from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST


def say_hello(request):
    """Welcome page (name entry)."""
    return render(request, 'core/welcome.html')


@require_POST
def save_name(request):
    """Saves the student's name in their session, then tells the page where to go."""
    name = request.POST.get('name', '').strip()[:50]
    if not name:
        return JsonResponse({'ok': False, 'error': 'Please enter your name.'}, status=400)

    request.session['user_name'] = name
    return JsonResponse({'ok': True, 'redirect': reverse('dashboard')})


def dashboard(request):
    name = request.session.get('user_name')
    if not name:
        # Nobody entered a name yet -> send them back to the welcome page
        return redirect('welcome')

    # Placeholder until the ML model is connected.
    # Later: request.session['stress_score'] = model_prediction (0-100)
    score = request.session.get('stress_score')  # None = not assessed yet

    if score is None:
        level = None
    elif score < 25:
        level = 'Normal'
    elif score < 50:
        level = 'Mild'
    elif score < 75:
        level = 'Moderate'
    else:
        level = 'High Risk'

    context = {
        'user_name': name,
        'stress_score': score,
        'stress_level': level,
    }
    return render(request, 'core/dashboard.html', context)


def change_name(request):
    """Lets the student start over with a different name."""
    request.session.flush()
    return redirect('welcome')
