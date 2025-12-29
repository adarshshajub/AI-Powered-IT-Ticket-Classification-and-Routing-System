import logging
from celery import shared_task
from tickets.utils.mailer import send_email_reply
from tickets.models import Ticket, EmailTicket
from django.db.models import Q

logger = logging.getLogger(__name__)

@shared_task
def send_email_replay_with_ticket():
    tickets = Ticket.objects.exclude(Q(servicenow_ticket_number__isnull=True)| Q(email_record__reply_sent=True))
    account_key = "support"
    if tickets is not None:
        for ticket in tickets:
            email = getattr(ticket, 'email_record', None)
            if email is not None:
                logger.debug(f"Sending email reply to {email.sender} with ticket number.")
                ticket_number = ticket.servicenow_ticket_number
                if ticket_number:
                    send_email_reply(account_key, ticket_number, email.sender, email.subject)
                    logger.debug(f"Email reply sent to {email.sender} for Ticket #{ticket.id}")
    else:
        logger.debug("All email replay are sent")

