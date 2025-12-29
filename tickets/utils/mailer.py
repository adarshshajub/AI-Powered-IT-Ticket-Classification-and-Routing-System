import logging
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives, get_connection
from tickets.models import EmailTicket

"""Utility functions for sending emails using different email tickets configured in Django settings."""

logger = logging.getLogger(__name__)

# create SMTP connection based on account key
def get_smtp_connection(account_key):
    accounts = getattr(settings, "EMAIL_ACCOUNTS", {})
    if account_key not in accounts:
        raise ValueError(
            f"Email account '{account_key}' is not configured in settings.EMAIL_ACCOUNTS"
        )
    config = accounts[account_key]
    return get_connection(
        host=settings.EMAIL_HOST,
        port=settings.EMAIL_PORT,
        username=config["EMAIL_HOST_USER"],
        password=config["EMAIL_HOST_PASSWORD"],
        use_tls=settings.EMAIL_USE_TLS,
        use_ssl=settings.EMAIL_USE_SSL,
        fail_silently=False,
    )

#send replay email for email ticket submission
def send_email_reply(
    account_key,
    ticket_number,
    to_email,
    subject,
    subject_template="email/replay_email_subject.txt",
    email_template_txt="email/replay_email.txt",
    email_template_html="email/replay_email.html",
):
    email_subject = f"Re: {subject} - Ticket Created: {ticket_number}"
    logger.debug(
        f"Preparing to send reply email for ticket {ticket_number} to {email_subject}"
    )
    context = {
        "ticket_number": ticket_number,
        "subject": email_subject,
    }

    if account_key not in settings.EMAIL_ACCOUNTS:
        raise ValueError(f"Email account '{account_key}' is not configured.")

    subject = render_to_string(subject_template, context).strip()
    text_body = render_to_string(email_template_txt, context)
    html_body = render_to_string(email_template_html, context)
    cfg = settings.EMAIL_ACCOUNTS[account_key]

    connection = get_smtp_connection(account_key)
    try:
        msg = EmailMultiAlternatives(
            subject,
            text_body,
            cfg["EMAIL_HOST_USER"],
            [to_email],
            connection=connection,
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send(fail_silently=False)
    except Exception as e:
        logger.error(
            f"Failed to send reply email to {to_email} for ticket {ticket_number}: {str(e)}"
        )
        raise

    EmailTicket.objects.update(reply_sent=True)
    logger.info(
        f"Reply email sent successfully to {to_email} for ticket {ticket_number}.")
