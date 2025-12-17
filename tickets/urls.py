from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views

"""Defines URL patterns for the ticket automation system."""

urlpatterns = [
    path('', views.home, name='home'),
    # path('account/register/', views.register, name='register'),
    path('account/signup/', views.SignUpView.as_view(), name='signup'),
    path('account/verify/<uidb64>/<token>/', views.verify_email, name='verify_email'),
    path('account/resend-verification/', views.ResendVerificationView.as_view(), name='resend_verification'),
    path('account/login/', auth_views.LoginView.as_view(template_name='registration/login.html', redirect_authenticated_user=True), name='login'),
    path('account/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('account/profile/', views.profile, name='profile'),
    path('account/profile/password_change/', views.PasswordChangeView.as_view(), name='password_change'),
    path('account/profile/password_reset/', views.PasswordResetView.as_view(), name='password_reset'),
    path('account/reset/<uidb64>/<token>/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('tickets/list/', views.ticket_list, name='ticket_list'),
    path("tickets/detail/<int:ticket_id>/", views.ticket_detail, name="ticket_detail"),
    path('tickets/<int:ticket_id>/edit/', views.ticket_edit, name='ticket_edit'),
    path('tickets/create/', views.ticket_create, name='create_ticket'),
    path('tickets/<int:ticket_id>/processing/', views.ticket_processing, name='ticket_processing'),
    path('tickets/<int:ticket_id>/success/', views.ticket_success, name='ticket_success'),
    path('tickets/<int:ticket_id>/error/', views.ticket_error, name='ticket_error'),
    path('tickets/<int:ticket_id>/retry/', views.retry_ticket, name='retry_ticket'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('my-dashboard/', views.user_dashboard, name='user_dashboard'),
    path('tickets/admin-ticket-update/<int:ticket_id>/', views.admin_update_ticket, name='admin_update_ticket'),
    path('api/ticket/<int:ticket_id>/status/', views.check_ticket_status_api, name='ticket_status_api'),
]