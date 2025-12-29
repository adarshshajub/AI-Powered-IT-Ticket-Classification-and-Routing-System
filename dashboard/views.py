import logging
import json
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from tickets.models import Ticket
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import timedelta
from django.db.models import Count,Avg, F
from django.utils.safestring import mark_safe
from django.db.models.functions import TruncDate

logger = logging.getLogger(__name__)


# Admin dashboard view with stats and charts
def admin_dashboard(request):
    logger.info("Admin dashboard accessed.")
    if request.user.is_staff:
        tickets_qs = Ticket.objects.all().order_by("-created_at")
        category = request.GET.get("category")
        status = request.GET.get("status")
        q = request.GET.get("q")

        if category:
            tickets_qs = tickets_qs.filter(category=category)

        if status:
            tickets_qs = tickets_qs.filter(ticket_creation_status=status)

        if q:
            tickets_qs = tickets_qs.filter(title__icontains=q) | tickets_qs.filter(
                description__icontains=q
            )

        # Pagination
        paginator = Paginator(tickets_qs, 10)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)


        total_tickets = Ticket.objects.count()
        new_tickets = Ticket.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=1)
        ).count()
        open_tickets = Ticket.objects.exclude(
            servicenow_ticket_status__in=["Closed", "Resolved", "Canceled"]
        ).count()
        snow_synced = Ticket.objects.filter(ticket_creation_status="created").count()

        failed_tickets = Ticket.objects.filter(ticket_creation_status="failed").count()

        pending_tickets = Ticket.objects.filter(ticket_creation_status="pending").count()

        email_tickets = Ticket.objects.filter(request_type="email").count()

        # Category Doughnut Chart
        CATEGORY_ORDER = [c[0] for c in Ticket.CATEGORY_CHOICES]
        CATEGORY_LABELS = {c[0]: c[1] for c in Ticket.CATEGORY_CHOICES}

        raw_counts = (
            Ticket.objects.exclude(category__isnull=True)
            .exclude(category__exact="")
            .values("category")
            .annotate(count=Count("id"))
        )

        counts_map = {
            row["category"].strip().lower(): row["count"] for row in raw_counts
        }

        category_labels = []
        category_counts = []

        for key in CATEGORY_ORDER:
            category_labels.append(CATEGORY_LABELS[key])
            category_counts.append(int(counts_map.get(key, 0)))

        # Time-Series Chart (Last 30 Days)
        today = timezone.now().date()
        start_date = today - timedelta(days=29)

        raw_time_counts = (
            Ticket.objects
            .filter(created_at__date__gte=start_date)
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(count=Count("id"))
        )

        # Build map
        time_count_map = {
            row["day"]: row["count"]
            for row in raw_time_counts
        }

        time_labels = []
        time_counts = []

        for i in range(30):
            day = start_date + timedelta(days=i)
            time_labels.append(day.strftime("%b %d"))
            time_counts.append(int(time_count_map.get(day, 0)))

    
        # Recent Tickets
        recent_tickets = Ticket.objects.order_by("-created_at")[:3]

        averages = tickets_qs.aggregate(
            avg_category=Avg('category_confidence'),
            avg_priority=Avg('priority_confidence')
        )

        category_model_accuracy = round(averages['avg_category'],3)
        priority_model_accuracy = round(averages['avg_priority'],3)

        created_count = snow_synced
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



        # Context
        context = {
            # summary
            "total_tickets": total_tickets,
            "new_tickets": new_tickets,
            "open_tickets": open_tickets,
            "snow_synced": snow_synced,
            "failed_tickets":failed_tickets,
            "pending_tickets":pending_tickets,
            "email_tickets":email_tickets,
            "snow_success_rate":snow_success_rate,
            "snow_last_sync":snow_last_sync,
            "last_updated": timezone.now(),
            "category_model_accuracy":category_model_accuracy,
            "priority_model_accuracy":priority_model_accuracy,
            # charts
            "category_labels": json.dumps(category_labels),
            "category_counts": json.dumps(category_counts),
            "time_labels": json.dumps(time_labels),
            "time_counts": json.dumps(time_counts),
            # table
            "tickets": page_obj,
            "recent_tickets": recent_tickets,
            "is_paginated": page_obj.has_other_pages(),
            "page_obj": page_obj,
            # misc
            "Ticket": Ticket,
        }

        return render(request, "admin_dashboard.html", context)
    else:
        return redirect("dashboard:user_dashboard")


# User dashboard view with personal stats
@login_required
def user_dashboard(request):
    user = request.user
    if user.is_staff:
        return redirect("dashboard:admin_dashboard")
    else:
        logger.info(f"User dashboard accessed by {user.username}")
        # Aggregates for current user
        total_by_user = Ticket.objects.filter(created_by=user).count()
        open_by_user = (
            Ticket.objects.filter(created_by=user)
            .exclude(servicenow_ticket_status__in=["Closed", "Resolved", "Cancelled"])
            .count()
        )
        resolved_issue = (
            Ticket.objects.filter(created_by=user)
            .filter(servicenow_ticket_status__in=["Closed", "Resolved", "Cancelled"])
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
