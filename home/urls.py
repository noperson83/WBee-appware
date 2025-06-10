# home/urls.py
"""
Simple Django 5 URL patterns for home app.
Only function-based views to avoid import errors.
"""

from django.urls import path
from . import views

app_name = 'home'

urlpatterns = [
    # Main dashboard
    path('', views.index, name='index'),
    
    # Contact functionality
    path('contact/', views.contactView, name='contact'),
    path('success/', views.successView, name='success'),
]