from django.core.management.base import BaseCommand
import requests
from django.conf import settings

class Command(BaseCommand):
    help = 'Create Service-now group'

    def handle(self, *args, **options):

        self.stdout.write("Loading config...")

        servicenow_instance = settings.SERVICENOW_INSTANCE
        servicenow_username = settings.SERVICENOW_USERNAME
        servicenow_password = settings.SERVICENOW_PASSWORD

        url = f"https://{servicenow_instance}.service-now.com/api/now/table/sys_user_group"
        AUTH = (servicenow_username, servicenow_password)

        self.stdout.write("Assigning the group names...")
        groups = [
            "Network Support",
            "Cloud Support",
            "Database Support",
            "Application Support",
            "Unix Support",
            "Security Support",
            "VM Support",
            "Storage Support",
            "Monitoring Support",
            "DevOps Support",
            "Hardware Support",
            "Email Support",
            "Backup Support",
            "Vendor Support"
        ]

        self.stdout.write("Connecting to service-now and creating the groups")
        for group in groups:
            payload = {
                "name": group,
                "description": f"{group} assignment group"
            }

            response = requests.post(
                url,
                auth=AUTH,
                json=payload
            )

            if response.status_code == 201:
                self.stdout.write(f"Created group: {group}")
            else:
                self.stdout.write(self.style.ERROR(f"Failed to create {group}: {response.text}"))