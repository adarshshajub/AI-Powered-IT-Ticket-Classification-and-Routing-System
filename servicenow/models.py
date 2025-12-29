from django.db import models

class AssignmentGroup(models.Model):
    """
    Stores ServiceNow assignment groups.
    """
    CATEGORY_CHOICES = [
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

    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        unique=True
    )
    servicenow_group_id = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name}" 