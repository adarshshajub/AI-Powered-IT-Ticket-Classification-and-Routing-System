from django import forms
from .models import Ticket


# Form for creating and updating tickets
class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['title', 'description']

# Form for admin to edit ticket details
class TicketAdminEditForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = [
            "title", 
            "description",
            "category",
            "assigned_team",
            "ticket_creation_status",
            "servicenow_ticket_number",
            "servicenow_ticket_status",
        ]

        widgets = {
            "description": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "assigned_team": forms.Select(attrs={"class": "form-select"}),
            "servicenow_ticket_number": forms.TextInput(attrs={"class": "form-control"}),
            "servicenow_ticket_status": forms.TextInput(attrs={"class": "form-control"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "ticket_creation_status": forms.Select(attrs={"class": "form-select"}),
        }


