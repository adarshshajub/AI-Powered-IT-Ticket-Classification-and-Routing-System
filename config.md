# Configuration & Setup Guide  
## AI Powered IT Ticket Automation System

This document explains **how to configure and run the project after cloning it from GitHub**.

---

## 1. Prerequisites

Ensure the following are installed on your system:

### System Requirements
- Python **3.10+** (recommended: 3.11)
- Git
- Docker account (required for Celery)
- ServiceNow Developer Instance (for integration)
- Email account 

### Verify Installation
```bash
python --version
git --version
docker --version
```

## 2. Clone the Repository
```bash
git clone https://github.com/adarshshajub/AI-Powered-IT-Ticket-Classification-and-Routing-System.git
cd AI-Powered-IT-Ticket-Classification-and-Routing-System
```

## 3. Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate
```

## 4. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## 5. Environment Configuration
Create a .env file in the project root:

```bash
SECRET_KEY = 'your-secret-key'
DJANGO_ALLOWED_HOSTS = "localhost, 127.0.0.1"
EMAIL_SMTP_HOST = 'smtp.gmail.com'  
EMAIL_SMTP_PORT = 587
SYSTEM_EMAIL_HOST_USER = 'your-email'
SYSTEM_EMAIL_HOST_PASSWORD = 'email-app-password'
SUPPORT_EMAIL_HOST_USER = 'your-email'
SUPPORT_EMAIL_HOST_PASSWORD = 'email-app-password'
EMAIL_IMAP_HOST = 'imap.gmail.com'
EMAIL_IMAP_PORT = 993
DEFAULT_SITE_SCHEME='http'
DEFAULT_SITE_DOMAIN='localhost:8000'
SERVICENOW_INSTANCE = 'your-servicenow-instance'
SERVICENOW_USERNAME = 'your-servicenow-instance-username'
SERVICENOW_PASSWORD = 'your-servicenow-instance-password'
SERVICENOW_SYSID= 'your-servicenow-instance-sysid'
```

## 6. Django Setup
Apply Migrations:
```bash
python manage.py makemigrations
python manage.py makemigrations account ai dashboard servicenow tickets 
python manage.py migrate
```

Create Superuser (For Admin login):
```bash
python manage.py createsuperuser
```
If you want to override email verification of superuser, run below commands in django shell. 
```bash
python manage.py shell
    from django.contrib.auth import get_user_model
    User = get_user_model()  
    user = User.objects.get(username="<your-superuser-name>")
    profile = getattr(user, "profile", None)
    profile.email_verified = True
    profile.save(update_fields=["email_verified"])
```


## 7. Start Redis (Required for Celery)
```bash
docker pull redis:latest
docker run -d --name my-redis -p 6379:6379 redis:latest
docker ps
```

## 8. Start Django Server
```bash
python manage.py runserver
```

## 9. Celery Configuration
```bash
celery -A AI_Powered_IT_Ticket_System worker -l info --pool=solo
```

## 10. Start Celery Beat (Scheduled Tasks)
```bash
celery -A AI_Powered_IT_Ticket_System beat -l info
```

## 11. Start Email Monitoring 
```bash
python manage.py mail_monitor
```

## 12. Add Service-now Group IDs 
- Login to admin dashboard and open Assignment Group edit
    (http://127.0.0.1:8000/service-now/admin/assignment-groups/)
- Add the Group Name and IDs from your service-now







