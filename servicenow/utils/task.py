import logging
from celery import shared_task
from django.utils import timezone
from tickets.models import Ticket
from servicenow.utils.servicenow import (
    create_servicenow_ticket,
    fetch_servicenow_ticket_status,
)
from django.db.models import Q

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
    retry_backoff=True,
    retry_jitter=True,
)
def process_ticket_task(self, ticket_id):
    """
    Celery task to sync ticket with ServiceNow.
    """
    ticket = Ticket.objects.get(id=ticket_id)

    try:
        logger.info(f"Celery processing ticket {ticket.id}")

        create_servicenow_ticket(ticket)

    except Exception as e:
        ticket.ticket_creation_status = "failed"
        ticket.sync_attempts += 1
        ticket.last_sync_attempt = timezone.now()
        ticket.error_message = str(e)
        ticket.save(
            update_fields=[
                "ticket_creation_status",
                "sync_attempts",
                "last_sync_attempt",
                "error_message",
            ]
        )

        logger.exception(f"Celery failed for ticket {ticket.id}")
        raise


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=30,
    retry_kwargs={"max_retries": 3},
)
def sync_servicenow_ticket_statuses(self):
    """
    Periodically sync ServiceNow ticket status into local DB
    """
    tickets = Ticket.objects.exclude(
        Q(servicenow_sys_id__isnull=True)
        | Q(servicenow_ticket_status__in=["Resolved", "Closed", "Canceled"])
    )

    logger.info(f"Starting ServiceNow status sync for {tickets.count()} tickets")

    try:
        for ticket in tickets:
            sn_state = fetch_servicenow_ticket_status(ticket.servicenow_sys_id)
            if not sn_state:
                continue
            sn_state_normalized = sn_state.strip().lower()

            sn_state_choices = {
                "1": "New",
                "2": "In-Progress",
                "3": "On-Hold",
                "6": "Resolved",
                "7": "Closed",
                "8": "Canceled",
            }
            ticket.servicenow_ticket_status = sn_state_choices[str(sn_state_normalized)]
            logger.debug(
                f"ServiceNow State: {ticket.servicenow_ticket_status} for ticket - {ticket.servicenow_ticket_number}"
            )
            ticket.save()

        logger.info("ServiceNow status sync completed")
    except Exception as e:
        logger.exception(f"Status update failed: {e}")
        raise


@shared_task
def servicenow_ticket_retry():
    tickets = Ticket.objects.exclude(
        ticket_creation_status__in=["created","retrying"]
    )
    if tickets:
        logger.info("Servicenow sheduled retry started...")
        for ticket in tickets:
            process_ticket_task.delay(ticket.id)
            logger.debug(f"Creating servicenow ticket #{ticket.id}")
        logger.info("Servicenow sheduled retry completed")
    else:
        logger.info("No pending or failed request to create the servicenow ticket")