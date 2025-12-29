from django import forms
from servicenow.models import AssignmentGroup

class AssignmentGroupForm(forms.ModelForm):
    class Meta:
        model = AssignmentGroup
        fields = ["name", "servicenow_group_id", "category", "is_active"]

        CATEGORY_CHOICES = [
            ("", "Select Category"), 
            ("cloud", "Cloud"),
            ("unix", "Unix"),
            ("network", "Network"),
            ("database", "Database"),
            ("application", "Application"),
            ("security","Security"),
            ("virtualization","Virtualization"),
            ("storage", "Storage"),
            ("monitoring","Monitoring"),
            ("devops","DevOps"),
            ("hardware","Hardware"),
            ("email","Email"),
            ("backup","Backup"),
            ("vendor","Vendor"),
        ]

        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "servicenow_group_id": forms.TextInput(attrs={"class": "form-control"}),
            "category": forms.Select(choices=CATEGORY_CHOICES ,attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
