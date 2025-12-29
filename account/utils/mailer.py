import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.urls import reverse
from django.utils import timezone
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator

"""Utility functions for sending emails using different email accounts configured in Django settings."""

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


# send password reset email
def send_password_reset_email(
    account_key,
    request,
    user,
    subject_template,
    email_template_txt,
    email_template_html,
):
    try:
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        context = {
            "email": user.email,
            "domain": request.get_host(),
            "site_name": getattr(settings, "SITE_NAME", request.get_host()),
            "uid": uid,
            "user": user,
            "token": token,
            "protocol": request.scheme,
        }
        subject = render_to_string(subject_template, context).strip()
        text_body = render_to_string(email_template_txt, context)
        html_body = render_to_string(email_template_html, context)

        connection = get_smtp_connection(account_key)
        config = settings.EMAIL_ACCOUNTS[account_key]

        from_email = config["EMAIL_HOST_USER"]

        logger.info(
            f"Sending email via [{account_key}] as {from_email} to {user.email}"
        )

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=from_email,
            to=[user.email],
            reply_to=[from_email],
            connection=connection,
        )

        # Attach HTML body
        if html_body:
            msg.attach_alternative(html_body, "text/html")

        sent_count = msg.send()
        logger.info(
            f"Email sent via [{account_key}] to {user.email}. Count={sent_count}"
        )

        return True

    except Exception as e:
        logger.exception(f"Failed to send email via account '{account_key}': {e}")
        return False


#send verification email
def send_verification_email(
    account_key,
    request,
    user,
    subject_template="email/verify_email_subject.txt",
    email_template_txt="email/verify_email.txt",
    email_template_html="email/verify_email.html",
):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    path = reverse("account:verify_email", kwargs={"uidb64": uid, "token": token})
    verify_url = f"{request.scheme}://{request.get_host()}{path}"

    context = {
        "user": user,
        "verify_url": verify_url,
        "domain": request.get_host(),
        "protocol": request.scheme,
    }

    if account_key not in settings.EMAIL_ACCOUNTS:
        raise ValueError(f"Email account '{account_key}' is not configured.")

    subject = render_to_string(subject_template, context).strip()
    text_body = render_to_string(email_template_txt, context)
    html_body = render_to_string(email_template_html, context)
    cfg = settings.EMAIL_ACCOUNTS[account_key]

    connection = get_smtp_connection(account_key)

    msg = EmailMultiAlternatives(
        subject, text_body, cfg["EMAIL_HOST_USER"], [user.email], connection=connection
    )
    msg.attach_alternative(html_body, "text/html")
    msg.send(fail_silently=False)

    # Update the timestamp of when the verification email was sent
    try:
        profile = user.profile
        profile.verification_sent_at = timezone.now()
        profile.save(update_fields=["verification_sent_at"])
    except Exception:
        pass

# account creation and password reset email for the email users 
def send_mail_from_account(account_key, subject, text_body, html_body, to_emails):
    logger.debug(f"Preparing to send email to {to_emails}")
    if account_key not in settings.EMAIL_ACCOUNTS:
        raise ValueError(f"Email account '{account_key}' is not configured.")

    cfg = settings.EMAIL_ACCOUNTS[account_key]

    connection = get_smtp_connection(account_key)

    try:
        msg = EmailMultiAlternatives(
            subject,
            text_body,
            cfg["EMAIL_HOST_USER"],
            [to_emails],
            connection=connection,
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send(fail_silently=False)
        logger.info(
            f"Email sent successfully to {to_emails} for the account creation and password reset."
        )
    except Exception as e:
        logger.error(
            f"Failed to send email to {to_emails} via account '{account_key}': {e}"
        )
        raise
