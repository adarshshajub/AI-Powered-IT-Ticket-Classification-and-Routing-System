import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "AI_Powered_IT_Ticket_System.settings")

app = Celery("AI_Powered_IT_Ticket_System", include=["tickets.utils.task","servicenow.utils.task"])

app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
