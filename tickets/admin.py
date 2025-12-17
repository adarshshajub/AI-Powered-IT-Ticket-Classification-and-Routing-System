from django.contrib import admin
from .models import Ticket, EmailTicket

"""Admin configuration for Ticket and EmailTicket models."""

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "category",
        "ticket_creation_status",
        "assigned_team",
        "servicenow_ticket_number",
        "created_at",
    )
    list_filter = ("category", "ticket_creation_status")
    search_fields = (
        "title",
        "description",
        "assigned_team",
        "servicenow_ticket_number",
    )
    list_editable = (
        "assigned_team",
        "ticket_creation_status",
        "servicenow_ticket_number",
    )


@admin.register(EmailTicket)
class EmailTicketAdmin(admin.ModelAdmin):
    list_display = ("uid", "sender", "subject", "received_at", "reply_sent", "ticket")
    search_fields = ("uid", "sender", "subject")
    raw_id_fields = ("ticket",)
