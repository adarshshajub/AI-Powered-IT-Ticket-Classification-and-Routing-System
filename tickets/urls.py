from django.urls import path 
from . import views

"""Defines URL patterns for the ticket management system."""

app_name = 'tickets'

urlpatterns = [
    path('list/', views.ticket_list, name='ticket_list'),
    path('detail/<int:ticket_id>/', views.ticket_detail, name="ticket_detail"),
    path('<int:ticket_id>/edit/', views.ticket_edit, name='ticket_edit'),
    path('create/', views.ticket_create, name='create_ticket'),
    path('<int:ticket_id>/processing/', views.ticket_processing, name='ticket_processing'),
    path('<int:ticket_id>/success/', views.ticket_success, name='ticket_success'),
    path('<int:ticket_id>/error/', views.ticket_error, name='ticket_error'),
    path('<int:ticket_id>/retry/', views.retry_ticket, name='retry_ticket'),    
    path('admin-ticket-update/<int:ticket_id>/', views.admin_update_ticket, name='admin_update_ticket'),
    path('api/<int:ticket_id>/status/', views.check_ticket_status_api, name='ticket_status_api'),
]