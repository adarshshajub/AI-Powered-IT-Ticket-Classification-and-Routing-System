from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Ticket
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model

"""Forms for the AI-Powered IT Ticket Automation System."""

User = get_user_model()

# Form for user sign-up
class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

# Form for creating and updating tickets
class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['title', 'description']

# Form for updating user profile
class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']

        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter username'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter email'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter first name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter last name'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.get('instance')  # logged-in user
        super().__init__(*args, **kwargs)

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.exclude(pk=self.user.pk).filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.exclude(pk=self.user.pk).filter(email=email).exists():
            raise forms.ValidationError("This email is already in use.")
        return email
    
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
            "assigned_team": forms.TextInput(attrs={"class": "form-control"}),
            "servicenow_ticket_number": forms.TextInput(attrs={"class": "form-control"}),
            "servicenow_ticket_status": forms.TextInput(attrs={"class": "form-control"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "ticket_creation_status": forms.Select(attrs={"class": "form-select"}),
        }