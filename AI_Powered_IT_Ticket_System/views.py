import logging
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from tickets.models import Ticket

logger = logging.getLogger(__name__)


# Home view - redirect based on role and ticket existence
@login_required
def home(request):
    logger.info("Home view accessed")
    # if user is admin redirect to admin dashboard else user dashboard
    if request.user.is_staff:
        logger.info("Admin user detected, redirecting to admin dashboard.")
        return redirect("dashboard:admin_dashboard")
    else:
        # if ticket exsits defalut to dashboard else create ticket
        if Ticket.objects.filter(created_by=request.user).exists():
            logger.info(
                "Existing tickets found for user, redirecting to user dashboard."
            )
            return redirect("dashboard:user_dashboard")
        else:
            logger.info(
                "No existing tickets found for user, redirecting to ticket creation."
            )
            return redirect("tickets:create_ticket")