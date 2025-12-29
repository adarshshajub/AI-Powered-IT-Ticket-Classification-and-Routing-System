import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from .forms import SignUpForm, CustomLoginForm, UserUpdateForm, AdminUserUpdateForm 
from django.views import View
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django import forms
from .utils.mailer import send_verification_email, send_password_reset_email
from django.utils import timezone
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse_lazy
from django.contrib.auth import views as auth_views
from django.http import BadHeaderError
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)
User = get_user_model()

# User registration view
class SignUpView(View):
    template_name = "registration/signup.html"

    def get(self, request):
        form = SignUpForm()
        if request.user.is_authenticated:
            return redirect("home")
        else:
            return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = SignUpForm(request.POST)
        if request.user.is_authenticated:
            return redirect("home")
        else:
            if form.is_valid():
                user = form.save(commit=False)
                # set inactive until verified
                user.is_active = False
                # ensure email stored
                user.email = form.cleaned_data["email"]
                user.save()

                try:
                    logger.info(f"Sending verification email to {user.email}")
                    send_verification_email("system", request, user)
                except Exception as e:
                    logger.error(f"Error sending verification email: {e}")
                    messages.error(
                        request, "Error sending verification email. Contact admin."
                    )
                    return redirect("account:signup")

                messages.success(
                    request,
                    "Account created. Please check your email to verify your account.",
                )
                return redirect("account:login")
            return render(request, self.template_name, {"form": form})

# User login view 
class CustomLoginForm(LoginView):
    authentication_form = CustomLoginForm
    template_name = "registration/login.html"

# Email verification view
def verify_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except Exception:
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        profile = getattr(user, "profile", None)
        if profile:
            profile.email_verified = True
            profile.save(update_fields=["email_verified"])
        user.is_active = True
        user.save(update_fields=["is_active"])
        messages.success(request, "Email verified. You can now login.")
        return redirect("account:login")

    # Token invalid/expired: show a page that allows user to resend
    # You can prefill the resend form with user's email if user is not None
    prefill_email = user.email if user else ""
    return render(
        request, "registration/verification_failed.html", {"email": prefill_email}
    )

# Resend verification email view form 
class ResendVerificationForm(forms.Form):
    email = forms.EmailField()

# Resend verification email view
class ResendVerificationView(View):
    template_name = "registration/resend_verification.html"  # simple form

    def get(self, request):
        form = ResendVerificationForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = ResendVerificationForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        email = form.cleaned_data["email"].strip()
        users = User.objects.filter(email__iexact=email, is_active=False)

        if not users.exists():
            # For privacy don't reveal whether email exists; still show success message
            messages.info(
                request,
                "If that email exists and is unverified, a verification link was sent.",
            )
            return redirect("login")

        # send to each matching inactive user (usually one)
        sent_any = False
        for user in users:
            profile = getattr(user, "profile", None)
            # Rate-limit: e.g., 5 minutes minimum between sends
            if profile and profile.verification_sent_at:
                elapsed = timezone.now() - profile.verification_sent_at
                if elapsed.total_seconds() < 300:  # 300s = 5 minutes
                    # skip sending and inform user to wait
                    messages.info(
                        request,
                        "A verification was recently sent. Please wait a few minutes before requesting again.",
                    )
                    return redirect("login")

            try:
                send_verification_email("system", request, user)
                sent_any = True
            except Exception as e:
                # log real exception, but show generic info to user
                logger.exception("Error resending verification to %s", user.email)

        # Always respond same way to avoid leaking existence
        if sent_any:
            messages.success(
                request,
                "If the email exists and is unverified, a verification link has been sent.",
            )
        else:
            messages.info(
                request,
                "If the email exists and is unverified, a verification link was sent.",
            )
        return redirect("login")

    def get(self, request):
        form = ResendVerificationForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = ResendVerificationForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            users = User.objects.filter(email__iexact=email, is_active=False)
            for u in users:
                try:
                    send_verification_email("system", request, u)
                except Exception:
                    pass
            messages.info(
                request,
                "If that email exists and is unverified, a verification link was sent.",
            )
            return redirect("account:login")
        return render(request, self.template_name, {"form": form})


# Password change view
class PasswordChangeView(LoginRequiredMixin, auth_views.PasswordChangeView):
    logger.info("Password change view accessed.")
    template_name = "registration/password_change.html"
    success_url = reverse_lazy("account:profile")

    def form_valid(self, form):
        try:
            messages.success(self.request, "Your password was changed successfully.")
            logger.info(
                f"Password changed successfully for user: {self.request.user.username}"
            )
        except Exception as e:
            messages.error(self.request, "Password change failed. Please try again.")
            logger.error("Error during password change: %s", e)
        return super().form_valid(form)

# Password reset request view
class PasswordResetView(auth_views.PasswordResetView):
    logger.info("Password reset view accessed.")
    # template_name = "email/password_reset_request.html"
    email_template_name = "email/password_reset_email_content.txt"
    html_email_template_name = "email/password_reset_email_content.html"
    subject_template_name = "email/password_reset_subject_content.txt"
    success_url = reverse_lazy("account:login")  # redirect to login after reset request

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        logger.info(f"Password reset requested for email: {email}")

        try:
            users = list(form.get_users(email))
        except Exception as e:
            logger.exception("Error getting users for password reset: %s", e)
            users = []

        if not users:
            # Keep behavior quiet — don't reveal whether the email exists
            logger.info(
                "Password reset requested for %s: no matching active users found.",
                email,
            )
            messages.info(
                self.request,
                "If the email exists, password reset instructions have been sent.",
            )
            return redirect(self.get_success_url())

        sent_any = False
        for user in users:
            try:
                send_password_reset_email(
                    "system",
                    self.request,
                    user,
                    subject_template=self.subject_template_name,
                    email_template_txt=self.email_template_name,
                    email_template_html=self.html_email_template_name,
                )
                sent_any = True
                logger.info("Password reset email sent to %s", user.email)
            except BadHeaderError:
                logger.exception(
                    "BadHeaderError when sending password reset to %s", user.email
                )
            except Exception as e:
                logger.exception(
                    "Error sending password reset email to %s: %s", user.email, e
                )

        # Always return the same user-visible message to avoid info leak
        if sent_any:
            messages.info(
                self.request,
                "If the email exists, password reset instructions have been sent.",
            )
        else:
            messages.error(
                self.request,
                "There was an issue sending the reset email. Please try again later.",
            )

        # Continue with the normal post-flow (this will redirect to success_url)
        return redirect(self.get_success_url())

# Password reset confirm view
class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = "registration/password_reset.html"
    success_url = reverse_lazy("account:login")

    def form_valid(self, form):
        messages.success(
            self.request,
            "Password has been reset. You can now log in with the new password.",
        )
        return super().form_valid(form)

# User profile view
@login_required
def profile(request):
    logger.info("Profile view accessed.")
    user = request.user

    if request.method == "POST":
        form = UserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("account:profile")  # change if your url name differs
        else:
            messages.error(request, "Please correct the highlighted errors.")
    else:
        form = UserUpdateForm(instance=user)
    return render(request, "registration/profile.html", {"form": form})


def is_admin(user):
    return user.is_authenticated and user.is_staff

@user_passes_test(is_admin)
def admin_user_list(request):
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'admin/users/user_list.html', {'users': users})


@user_passes_test(is_admin)
def admin_user_edit(request, user_id):
    user = get_object_or_404(User, pk=user_id)

    if request.method == 'POST':
        form = AdminUserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "User updated successfully.")
            return redirect('account:admin_user_list')
    else:
        form = AdminUserUpdateForm(instance=user)

    return render(request, 'admin/users/user_edit.html', {
        'form': form,
        'user_obj': user
    })


@user_passes_test(is_admin)
@require_POST
def admin_user_delete(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    user.delete()
    messages.success(request, "User deleted successfully.")
    return redirect('account:admin_user_list')

    