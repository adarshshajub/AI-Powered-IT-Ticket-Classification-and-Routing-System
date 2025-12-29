import re
from django.contrib.auth import get_user_model
import secrets
import string
from django.db import transaction
from django.utils.http import urlsafe_base64_encode
from django.urls import reverse
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.encoding import force_bytes
from account.utils.mailer import send_mail_from_account
import logging

"""Utility functions for user management based on email addresses"""

logger = logging.getLogger(__name__)

User = get_user_model()

# Helper function to slugify and limit username length
def slugify_username(base: str) -> str:
    base = base.lower()
    # keep safe chars only
    base = re.sub(r"[^a-z0-9._-]+", "", base)
    return base[:30] or "user"

# Generate a unique username based on email local part
def generate_unique_username(email: str) -> str:
    local_part = email.split("@")[0]
    base = slugify_username(local_part)
    username = base
    suffix = 0
    while User.objects.filter(username=username).exists():
        suffix += 1
        username = f"{base}{suffix}"
        if len(username) > 30:
            username = username[:28] + str(suffix)  
    return username

# Generate a secure temporary password
def generate_temporary_password(length=12) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*-_"
    # ensure at least one lower, one upper, one digit
    while True:
        pwd = "".join(secrets.choice(alphabet) for _ in range(length))
        if (
            any(c.islower() for c in pwd)
            and any(c.isupper() for c in pwd)
            and any(c.isdigit() for c in pwd)
        ):
            return pwd

# Main function to get or create user by email
def get_or_create_user_by_email(email_address, send_welcome, account_key):
    logger.debug(f"Attempting to get or create user for email: {email_address}")
    logger.debug(f"Checking if user with email {email_address} exists.")
    if User.objects.filter(email__iexact=email_address).exists():
        user = User.objects.get(email__iexact=email_address)
        logger.debug(
            f"User with email {email_address} already exists. User ID: {user.id}"
        )
        return user, None

    logger.debug(f"No existing user found with email {email_address}.")
    username = generate_unique_username(email_address)
    temp_password = generate_temporary_password()
    logger.debug(f"Generated username: {username} and passoword: ******")

    logger.debug(
        f"Creating new user with email {email_address} and username {username}."
    )
    with transaction.atomic():
        user = User.objects.create_user(
            username=username, email=email_address, password=temp_password
        )
    logger.debug(f"User created with ID: {user.id}")

    # Mark email as verified and activate user for email users
    profile = getattr(user, "profile", None)
    if profile:
        profile.email_verified = True
        profile.save(update_fields=["email_verified"])
    user.is_active = True
    user.save(update_fields=["is_active"])
    
    # Build a one-time password-change/reset URL (so they can click to set new password)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)

    # Use your password reset confirm route name or custom change link
    reset_path = reverse(
        "account:password_reset_confirm", kwargs={"uidb64": uid, "token": token}
    )
    reset_url = f"{settings.DEFAULT_SITE_SCHEME or 'https'}://{settings.DEFAULT_SITE_DOMAIN or settings.ALLOWED_HOSTS[0]}{reset_path}"

    if send_welcome:
        ctx = {
            "user": user,
            "reset_url": reset_url,
        }
        subject = render_to_string(
            "email/new_email_user_subject.txt", ctx
        ).strip()
        text_body = render_to_string("email/new_email_user.txt", ctx)
        html_body = render_to_string("email/new_email_user.html", ctx)

        # send email using your mailer helper
        logger.debug(f"Sending welcome email to {email_address}.")
        send_mail_from_account(
            account_key=account_key,
            subject=subject,
            text_body=text_body,
            html_body=html_body,
            to_emails=email_address,
        )
        logger.debug(f"Welcome email sent to {email_address}.")
    return user, reset_url
