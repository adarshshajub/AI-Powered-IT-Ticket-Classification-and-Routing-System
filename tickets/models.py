from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

"""Models for IT Ticket Automation System"""

# Ticket model to store IT ticket details
class Ticket(models.Model):
    CATEGORY_CHOICES = [
        ("cloud", "Cloud"),
        ("unix", "Unix"),
        ("network", "Network"),
        ("database", "Database"),
        ("application", "Application"),
    ]
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("created", "Created"),
        ("failed", "Failed"),
        ("retrying", "Retrying"),
    ]
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="tickets"
    )
    assigned_team = models.CharField(max_length=100, blank=True)
    ticket_creation_status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending"
    )
    servicenow_ticket_number = models.CharField(max_length=100, blank=True, null=True)
    servicenow_ticket_status = models.CharField(
        max_length=100, blank=True, default="queued"
    )
    servicenow_sys_id = models.CharField(max_length=100, blank=True, null=True)
    assignment_group_id = models.CharField(
        max_length=100, blank=True, null=True
    )  # Store group sys_id
    sync_attempts = models.IntegerField(default=0)
    last_sync_attempt = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)
    request_type = models.CharField(
        max_length=20, choices=[("web", "Web"), ("email", "Email")], default="web"
    )

    def __str__(self):
        return f"Issue: {self.title} - Ticket: {self.servicenow_ticket_number} - Status: {self.ticket_creation_status}"


User = get_user_model()

# UserProfile model to extend User with email verification status
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    email_verified = models.BooleanField(default=False)
    verification_sent_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"profile for {self.user.get_username()}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


class EmailTicket(models.Model):
    uid = models.CharField(
        max_length=255, unique=True, help_text="Unique email message id / UID from IMAP"
    )
    sender = models.EmailField(blank=True, null=True)
    subject = models.CharField(max_length=255, blank=True, null=True)
    body = models.TextField(blank=True, null=True)
    raw_email = models.TextField(blank=True, null=True)
    received_at = models.DateTimeField(auto_now_add=True)
    reply_sent = models.BooleanField(default=False)

    # Link to Ticket: one-to-one (email -> ticket)
    ticket = models.OneToOneField(
        Ticket,
        on_delete=models.CASCADE,
        related_name="email_record",
        null=True,
        blank=True,
        help_text="Related Ticket created from this email",
    )

    class Meta:
        ordering = ["-received_at"]
        indexes = [
            models.Index(fields=["uid"]),
        ]

    def __str__(self):
        # show subject or fallback to uid
        return f"{self.subject or self.uid} — {self.sender or '-'}"
