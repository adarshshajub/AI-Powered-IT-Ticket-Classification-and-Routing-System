import logging
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse_lazy, reverse
from .forms import SignUpForm, TicketForm, UserUpdateForm, TicketAdminEditForm
from .models import Ticket, EmailTicket
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Count, Q
from django.utils.safestring import mark_safe
from datetime import timedelta
from django.views.decorators.http import require_POST
from django.core.exceptions import PermissionDenied
from django.http import BadHeaderError, JsonResponse
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth import get_user_model
from django.views import View
from .utils.mailer import (
    send_verification_email,
    send_password_reset_email,
    send_email_reply,
)
from django.views.generic import TemplateView
from django.template.loader import render_to_string
from django import forms
from django.utils import timezone
from django.db import transaction

""" Views for AI-Powered IT Ticket Automation System """

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
                # IMPORTANT: set inactive until verified
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
                    return redirect("signup")

                messages.success(
                    request,
                    "Account created. Please check your email to verify your account.",
                )
                return redirect("login")
            return render(request, self.template_name, {"form": form})


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
        return redirect("login")

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
            return redirect("login")
        return render(request, self.template_name, {"form": form})


# Home view - redirect based on role and ticket existence
@login_required
def home(request):
    logger.info("Home view accessed")
    # if user is admin redirect to admin dashboard else user dashboard
    if request.user.is_staff:
        logger.info("Admin user detected, redirecting to admin dashboard.")
        return redirect("admin_dashboard")
    else:
        # if ticket exsits defalut to dashboard else create ticket
        if Ticket.objects.filter(created_by=request.user).exists():
            logger.info(
                "Existing tickets found for user, redirecting to user dashboard."
            )
            return redirect("user_dashboard")
        else:
            logger.info(
                "No existing tickets found for user, redirecting to ticket creation."
            )
            return redirect("create_ticket")

# Ticket list view with filters and pagination
@login_required
def ticket_list(request):
    user = request.user
    logger.info("Ticket list view accessed.")
    page_number = request.GET.get("page", 1)
    if user.is_staff:
        all_user_qs = Ticket.objects.all().order_by("-created_at")
    else:
        all_user_qs = Ticket.objects.filter(created_by=user).order_by("-created_at")

    category_filter = request.GET.get("category", "").strip()
    status_filter = request.GET.get("status", "").strip()
    search_q = request.GET.get("q", "").strip()

    if category_filter:
        all_user_qs = all_user_qs.filter(category=category_filter)
    if status_filter:
        all_user_qs = all_user_qs.filter(ticket_creation_status=status_filter)
    if search_q:
        all_user_qs = all_user_qs.filter(
            Q(title__icontains=search_q)
            | Q(description__icontains=search_q)
            | Q(servicenow_ticket_number__icontains=search_q)
        )

    paginator = Paginator(all_user_qs, 10)  # 8 tickets per page
    page_obj = paginator.get_page(page_number)
    tickets_page = page_obj.object_list
    context = {
        "tickets": tickets_page,
        "is_paginated": page_obj.has_other_pages(),
        "page_obj": page_obj,
        "now": timezone.now(),
    }
    return render(request, "ticket_list.html", context)

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
            return redirect("profile")  # change if your url name differs
        else:
            messages.error(request, "Please correct the highlighted errors.")
    else:
        form = UserUpdateForm(instance=user)
    return render(request, "registration/profile.html", {"form": form})

# Password change view
class PasswordChangeView(LoginRequiredMixin, auth_views.PasswordChangeView):
    logger.info("Password change view accessed.")
    template_name = "registration/password_change.html"
    success_url = reverse_lazy("profile")

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
    template_name = "registration/password_reset_request.html"
    email_template_name = "registration/password_reset_email_content.txt"
    html_email_template_name = "registration/password_reset_email_content.html"
    subject_template_name = "registration/password_reset_subject_content.txt"
    success_url = reverse_lazy("login")  # redirect to login after reset request

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
    success_url = reverse_lazy("login")

    def form_valid(self, form):
        # response = super().form_valid(form)
        messages.success(
            self.request,
            "Password has been reset. You can now log in with the new password.",
        )
        return super().form_valid(form)


# create the ticket view from user input
@login_required
def ticket_create(request):
    logger.info("Ticket create view accessed.")
    if request.method == "POST":
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            # Predict category
            try:
                # predicted_category = predict_category(ticket.title, ticket.description)
                predicted_category = "cloud"  # Placeholder for actual prediction
                ticket.category = predicted_category
                logger.info(f"Predicted category: {predicted_category}")
            except Exception as e:
                logger.error(f"ML prediction failed: {e}")
                if not ticket.category:
                    ticket.category = "application"

            # Save with pending status
            ticket.ticket_creation_status = "pending"
            ticket.created_by = request.user
            ticket.save()

            logger.info(f"Ticket #{ticket.id} created")

            # Queue background task
            # sync_ticket_to_servicenow(ticket.id, schedule=0)

            # Redirect to waiting page that will poll for status
            return redirect("ticket_processing", ticket_id=ticket.id)
        else:
            logger.warning(f"Form validation failed: {form.errors}")
    else:
        form = TicketForm()

    return render(request, "submit_issues.html", {"form": form})

# create ticket from email
def email_ticket_create(email_uid, sender, subject, body, raw_email, user, account_key):
    logger.info("Email ticket view accessed.")

    # check if email ticket with uid already exists
    email_ticket = EmailTicket.objects.filter(uid=email_uid).first()
    if email_ticket and email_ticket.ticket:
        logger.debug(f"Email ticket with UID {email_uid} already exists.")
        return email_ticket.ticket, email_ticket

    # create the ticket if not exists
    # predicted_category = predict_category(ticket.title, ticket.description)
    predicted_category = "unix"  # Placeholder for actual prediction

    logger.debug(f"Creating ticket for email UID {email_uid} from sender {sender}")
    with transaction.atomic():
        ticket = Ticket.objects.create(
            title=subject[:200] if subject else "No subject",
            description=body or "",
            category=predicted_category or "",
            created_by=user,  # update to user later
            request_type="email",
        )
    logger.debug(f"Ticket #{ticket.id} created for email UID {email_uid}")

    logger.debug(f"Creating EmailTicket for UID {email_uid}")
    email_ticket, created = EmailTicket.objects.get_or_create(
        uid=email_uid,
        defaults={
            "sender": sender,
            "subject": subject,
            "body": body,
            "raw_email": raw_email,
            "ticket": ticket,
            "received_at": timezone.now(),
        },
    )
    logger.debug(f"EmailTicket for UID {email_uid} created.")

    logger.debug(f"Linking EmailTicket UID {email_uid} to Ticket #{ticket.id}")
    if not created and email_ticket.ticket is None:
        email_ticket.ticket = ticket
        email_ticket.save(update_fields=["ticket"])
        logger.debug(f"Linked EmailTicket UID {email_uid} to Ticket #{ticket.id}")

    logger.debug(f"Sending email reply to {sender} with ticket number.")
    ticket_number = Ticket.objects.filter(id=ticket.id).first().servicenow_ticket_number
    send_email_reply(account_key, ticket_number, sender, subject)
    logger.debug(f"Email reply sent to {sender} for Ticket #{ticket.id}")
    return ticket, email_ticket

# Ticket processing view - shows status while syncing
@login_required
def ticket_processing(request, ticket_id):
    logger.info(f"Ticket processing view accessed for ticket ID: {ticket_id}")
    ticket = get_object_or_404(Ticket, id=ticket_id)
    # If already processed, redirect to appropriate page
    if ticket.ticket_creation_status == "created":
        return redirect("ticket_success", ticket_id=ticket.id)
    elif ticket.ticket_creation_status == "failed":
        return redirect("ticket_error", ticket_id=ticket.id)

    context = {"ticket": ticket, "ticket_number": ticket.servicenow_ticket_number}

    return render(request, "processing.html", context)

# Ticket success view
@login_required
def ticket_success(request, ticket_id):
    logger.info(f"Ticket success view accessed for ticket ID: {ticket_id}")
    ticket = get_object_or_404(Ticket, id=ticket_id)
    # Ensure ticket is actually synced
    if ticket.ticket_creation_status != "created":
        return redirect("ticket_processing", ticket_id=ticket.id)
    context = {"ticket": ticket, "ticket_number": ticket.servicenow_ticket_number}
    return render(request, "success.html", context)

# Ticket success view
@login_required
def ticket_error(request, ticket_id):
    logger.info(f"Ticket error view accessed for ticket ID: {ticket_id}")
    ticket = get_object_or_404(Ticket, id=ticket_id)
    # Ensure ticket actually failed
    if ticket.ticket_creation_status == "created":
        return redirect("ticket_success", ticket_id=ticket.id)
    context = {
        "ticket": ticket,
        "error": ticket.error_message or "Failed to sync with ServiceNow",
    }

    return render(request, "error.html", context)

# Check ticket status API 
@login_required
def check_ticket_status_api(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)
    return JsonResponse(
        {
            "status": ticket.ticket_creation_status,
            "servicenow_number": ticket.servicenow_ticket_number,
            "sync_attempts": ticket.sync_attempts,
            "error_message": ticket.error_message,
        }
    )

# Retry ticket sync view
@login_required
def retry_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)

    if ticket.ticket_creation_status in ["failed", "pending"]:
        ticket.sync_attempts = 0
        ticket.ticket_creation_status = "pending"
        ticket.save()

        # sync_ticket_to_servicenow(ticket.id, retry_count=0, schedule=0)

        messages.success(request, f"Ticket #{ticket_id} queued for retry")
        return redirect("ticket_processing", ticket_id=ticket_id)
    else:
        messages.info(
            request, f"Ticket #{ticket_id} is already {ticket.ticket_creation_status}"
        )
        return redirect("ticket_list")

# Admin dashboard view with stats and charts
@staff_member_required
def admin_dashboard(request):
    logger.info("Admin dashboard accessed.")
    # --- Handle simple GET filters ---
    category_filter = request.GET.get("category", "").strip()
    status_filter = request.GET.get("status", "").strip()
    # days window for time-series charts (default 7)
    try:
        days = int(request.GET.get("days", 7))
        if days < 1 or days > 90:
            days = 7
    except ValueError:
        days = 7

    # Base queryset (all tickets)
    qs = Ticket.objects.all()

    # Apply filters
    if category_filter:
        qs = qs.filter(category=category_filter)
    if status_filter:
        qs = qs.filter(ticket_creation_status=status_filter)

    total_tickets = Ticket.objects.count()
    new_tickets = Ticket.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=1)
    ).count()
    filtered_total = qs.count()  # total after filter (for the table)
    pending_tickets = Ticket.objects.filter(ticket_creation_status="pending").count()
    created_tickets = Ticket.objects.filter(ticket_creation_status="created").count()
    failed_tickets = Ticket.objects.filter(ticket_creation_status="failed").count()
    # open = not final states (customize as needed)
    open_tickets = Ticket.objects.exclude(
        servicenow_ticket_status__in=["resolved", "closed", "cancelled"]
    ).count()
    email_tickets = Ticket.objects.filter(request_type="email").count()

    # Model accuracy placeholder - replace with real metric storage if available
    model_accuracy = getattr(request, "model_accuracy", None) or 87.5

    # Tickets by category (in choice order)
    cat_qs = Ticket.objects.values("category").annotate(count=Count("id"))
    CATEGORY_ORDER = [c[0] for c in Ticket.CATEGORY_CHOICES]
    CATEGORY_LABELS = {c[0]: c[1] for c in Ticket.CATEGORY_CHOICES}
    category_counts_map = {item["category"] or "": item["count"] for item in cat_qs}
    category_labels = [CATEGORY_LABELS.get(k, k.title()) for k in CATEGORY_ORDER]
    category_counts = [category_counts_map.get(k, 0) for k in CATEGORY_ORDER]

    # Tickets by assignment group (top 8)
    group_counts = (
        Ticket.objects.values("assignment_group_id", "assigned_team")
        .annotate(count=Count("id"))
        .order_by("-count")[:8]
    )

    # Top reporters (users who created most tickets) - requires created_by relation
    top_reporters = (
        Ticket.objects.values("created_by__username")
        .annotate(count=Count("id"))
        .order_by("-count")[:8]
    )

    # Time series: tickets per day for last `days`
    today = timezone.localdate()
    time_labels = []
    time_counts = []
    for i in range(days - 1, -1, -1):
        d = today - timedelta(days=i)
        time_labels.append(d.strftime("%b %d"))
        # Count using date part to be timezone-safe
        time_counts.append(Ticket.objects.filter(created_at__date=d).count())

    # Recent tickets and recent errors
    recent_tickets = Ticket.objects.order_by("-created_at")[:5]
    recent_errors = Ticket.objects.filter(ticket_creation_status="failed").order_by(
        "-last_sync_attempt"
    )[:10]

    # Paginated table (apply filters)
    page_number = request.GET.get("page", 1)
    paginator = Paginator(qs.order_by("-created_at"), 5)  # adjust per-page
    page_obj = paginator.get_page(page_number)
    tickets_page = page_obj.object_list

    # ServiceNow sync stats & success rate
    created_count = created_tickets
    failed_count = failed_tickets
    snow_success_rate = (
        round((created_count / (created_count + failed_count) * 100), 1)
        if (created_count + failed_count) > 0
        else 0
    )
    last_sync_obj = (
        Ticket.objects.exclude(last_sync_attempt__isnull=True)
        .order_by("-last_sync_attempt")
        .first()
    )
    snow_last_sync = last_sync_obj.last_sync_attempt if last_sync_obj else None

    # Keep query params for pagination links
    query_params = request.GET.copy()
    if "page" in query_params:
        query_params.pop("page")
    query_string = query_params.urlencode()

    context = {
        # counts
        "total_tickets": total_tickets,
        "new_tickets": new_tickets,
        "filtered_total": filtered_total,
        "pending_tickets": pending_tickets,
        "open_tickets": open_tickets,
        "created_tickets": created_tickets,
        "failed_tickets": failed_tickets,
        "email_tickets": email_tickets,
        # model / chart data
        "model_accuracy": model_accuracy,
        "category_labels": mark_safe(json.dumps(category_labels)),
        "category_counts": mark_safe(json.dumps(category_counts)),
        "time_labels": mark_safe(json.dumps(time_labels)),
        "time_counts": mark_safe(json.dumps(time_counts)),
        # lists
        "recent_tickets": recent_tickets,
        "recent_errors": recent_errors,
        "group_counts": group_counts,
        "top_reporters": top_reporters,
        # pagination & table
        "tickets": tickets_page,
        "is_paginated": page_obj.has_other_pages(),
        "page_obj": page_obj,
        "query_string": query_string,
        # ServiceNow metrics
        "snow_synced": created_count,
        "snow_errors": failed_count,
        "snow_last_sync": snow_last_sync,
        "snow_success_rate": snow_success_rate,
        # UI helpers
        "last_updated": timezone.now().strftime("%Y-%m-%d %H:%M"),
        "now": timezone.now(),
    }

    return render(request, "admin_dashboard.html", context)

# User dashboard view with personal stats
@login_required
def user_dashboard(request):
    user = request.user
    if user.is_staff:
        return redirect("admin_dashboard")
    else:
        logger.info(f"User dashboard accessed by {user.username}")
        # Aggregates for current user
        total_by_user = Ticket.objects.filter(created_by=user).count()
        open_by_user = (
            Ticket.objects.filter(created_by=user)
            .exclude(servicenow_ticket_status__in=["closed", "resolved", "cancelled"])
            .count()
        )
        resolved_issue = (
            Ticket.objects.filter(created_by=user)
            .filter(servicenow_ticket_status__in=["closed", "resolved", "cancelled"])
            .count()
        )
        recent_tickets = (
            Ticket.objects.filter(created_by=user).order_by("-created_at")[:1].count()
        )

        # Paginate user's all tickets (optional, for "my tickets" view on same page)
        page_number = request.GET.get("page", 1)
        all_user_qs = Ticket.objects.filter(created_by=user).order_by("-created_at")
        paginator = Paginator(all_user_qs, 6)
        page_obj = paginator.get_page(page_number)
        tickets_page = page_obj.object_list

        context = {
            "total_by_user": total_by_user,
            "open_by_user": open_by_user,
            "resolved_tickets": resolved_issue,
            "recent_tickets": recent_tickets,
            "tickets": tickets_page,
            "is_paginated": page_obj.has_other_pages(),
            "page_obj": page_obj,
            "now": timezone.now(),
        }
        return render(request, "user_dashboard.html", context)

# Ticket detail view
@login_required
def ticket_detail(request, ticket_id):
    logger.info(f"Ticket detail view accessed for ticket ID: {ticket_id}")
    ticket = get_object_or_404(Ticket, id=ticket_id)

    user_tickets = Ticket.objects.filter(created_by=request.user)
    if not request.user.is_staff and ticket not in user_tickets:
        raise PermissionDenied("You do not have permission to view this ticket.")

    return render(request, "ticket_detail.html", {"ticket": ticket})

# Admin ticket update view 
@staff_member_required
@require_POST
def admin_update_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, pk=ticket_id)

    # Read posted values (use .get to allow partial updates)
    status = request.POST.get("ticket_creation_status")
    assigned_team = request.POST.get("assigned_team")
    servicenow_ticket_number = request.POST.get("servicenow_ticket_number")

    changed = False

    # Validate status against defined choices
    if status is not None:
        valid_statuses = [s[0] for s in Ticket.STATUS_CHOICES]
        if status not in valid_statuses:
            if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
                return JsonResponse(
                    {"ok": False, "error": "invalid_status"}, status=400
                )
            else:
                raise ValidationError("Invalid status value")

        if status != ticket.ticket_creation_status:
            ticket.ticket_creation_status = status
            changed = True

    if assigned_team is not None and assigned_team != ticket.assigned_team:
        ticket.assigned_team = assigned_team
        changed = True

    if (
        servicenow_ticket_number is not None
        and servicenow_ticket_number != ticket.servicenow_ticket_number
    ):
        ticket.servicenow_ticket_number = servicenow_ticket_number
        changed = True

    if changed:
        ticket.save()

    # return JSON with a display label for status
    if request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest":
        # compute human-readable status (get_status_display assumes field is 'ticket_creation_status')
        try:
            status_display = ticket.get_ticket_creation_status_display()
        except Exception:
            # fallback: attempt generic get_<field>_display or just use the raw value
            status_display = getattr(ticket, "ticket_creation_status", "")

        return JsonResponse(
            {"ok": True, "ticket_id": ticket.pk, "status_display": status_display}
        )

    # fallback redirect to admin dashboard or referrer
    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or "/"
    return redirect(next_url)

# Admin ticket edit view
@staff_member_required
def ticket_edit(request, ticket_id):
    ticket = get_object_or_404(Ticket, pk=ticket_id)

    if request.method == "POST":
        form = TicketAdminEditForm(request.POST, instance=ticket)
        if form.is_valid():
            form.save()
            return redirect("ticket_detail", ticket.id)
    else:
        form = TicketAdminEditForm(instance=ticket)

    return render(request, "ticket_edit.html", {"form": form, "ticket": ticket})
