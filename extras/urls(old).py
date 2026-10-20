from django.urls import path
from . import views

urlpatterns = [
    path('', views.say_hello, name='welcome'),
    path('save-name/', views.save_name, name='save_name'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('change-name/', views.change_name, name='change_name'),
]
