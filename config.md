# Configuration & Setup Guide  
## AI Powered IT Ticket Automation System

This document explains **how to configure and run the project after cloning it from GitHub**.

---

## 1. Prerequisites

Ensure the following are installed on your system:

### System Requirements
- Python **3.10+** (recommended: 3.11)
- Git
- Redis (required for Celery)
- ServiceNow Developer Instance (for integration)
- Email account 

### Verify Installation
```bash
python --version
git --version
redis-server --version
```

## 2. Clone the Repository
- git clone https://github.com/adarshshajub/AI-Powered-IT-Ticket-Automation-System.git
- cd AI-Powered-IT-Ticket-Automation-System

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
python manage.py migrate
```

Create Superuser (For Admin login):
```bash
python manage.py createsuperuser
```

## 7. Start Redis (Required for Celery)
```bash
redis-server
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






