from django.urls import path 
from . import views

"""Defines URL patterns for the dashboard management system."""

app_name = 'dashboard'

urlpatterns = [   
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('my-dashboard/', views.user_dashboard, name='user_dashboard'),
]