from django.urls import path 
from . import views

"""Defines URL patterns for the service-now management system."""

app_name = 'servicenow'

urlpatterns = [
    path("admin/assignment-groups/", views.assignment_group_list, name="assignment_group_list"),
    path("admin/assignment-groups/add/", views.assignment_group_create, name="assignment_group_create"),
    path("admin/assignment-groups/<int:pk>/edit/", views.assignment_group_update, name="assignment_group_update"),
    path("admin/assignment-groups/<int:pk>/delete/", views.assignment_group_delete, name="assignment_group_delete"),
]