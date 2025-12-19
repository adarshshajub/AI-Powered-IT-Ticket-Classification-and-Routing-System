# AI-Powered IT Ticket Automation System

### An intelligent IT support automation platform that uses Machine Learning, NLP, and GenAI-assisted semantic embeddings to analyze user-reported issues (via web or email), automatically classify ticket categories and priorities, and integrate with ServiceNow for incident creation and routing.


## Overview
### Manual triaging of IT support tickets is time-consuming, inconsistent, and error-prone. This project automates the analysis, categorization, prioritization, and routing of IT issues using AI techniques, reducing manual effort and improving response times.

### The system supports:
	-> Web-based issue submission
	-> Email-based ticket creation
	-> AI-driven category & priority prediction
	-> Admin and user dashboards
	-> ServiceNow integration
	-> Secure authentication with email verification

### Key Features
#### User Features
	-> User registration with email verification
	-> Secure login with validation messages
	-> Submit IT issues via web portal
	-> View ticket status and ServiceNow details
	-> Profile management (update details, change password)
	-> Password reset via email

#### Admin Features
	-> Custom Admin Dashboard (outside Django Admin)
	-> View and manage all tickets
	-> Inline ticket updates (status, assignment, ServiceNow ID)
	-> Custom user management (list, edit, delete users)
	-> Monitor AI predictions and ServiceNow sync status

#### AI / ML Features

	-> Transformer-based semantic embeddings using Hugging Face SentenceTransformers
	-> Custom-trained ML models for:
		-> Ticket category prediction
		-> Ticket priority prediction
	-> Confidence-based AI predictions
	-> Designed for future continuous learning (human-in-the-loop)

#### Integrations

	-> ServiceNow REST API for incident creation
	-> Email integration (GMAIL SMTP) for:
		-> Password reset
		-> Email-based ticket intake
		-> Email verification



## Config:
### Ensure to create a '.env' file in-addition to the above code. This is to declare the environment calling in the setting.py file in the code.  
SECRET_KEY = '' <br>
DEBUG = <br>
DJANGO_ALLOWED_HOSTS = ""<br>
EMAIL_SMTP_HOST = ''  <br>
EMAIL_SMTP_PORT = <br>
EMAIL_USE_TLS = <br>
EMAIL_USE_SSL = <br>
SYSTEM_EMAIL_HOST_USER = '' <br>
SYSTEM_EMAIL_HOST_PASSWORD = '' <br>
SUPPORT_EMAIL_HOST_USER = '' <br>
SUPPORT_EMAIL_HOST_PASSWORD = '' <br>
EMAIL_IMAP_HOST = '' <br>
EMAIL_IMAP_PORT = <br>
DEFAULT_SITE_SCHEME='' <br>
DEFAULT_SITE_DOMAIN='' <br>

#### Example:
SECRET_KEY = 'django-insecure-=8ix5imku*t)ob&wtd=-he7xj9$df-)@22&zq2dq#1234' <br>
DEBUG = True <br>
DJANGO_ALLOWED_HOSTS = "localhost, 127.0.0.1" <br>
EMAIL_SMTP_HOST = 'smtp.gmail.com'  <br>
EMAIL_SMTP_PORT = 587 <br>
EMAIL_USE_TLS = True  <br>
EMAIL_USE_SSL = False <br>
SYSTEM_EMAIL_HOST_USER = 'abc@example.com' <br>
SYSTEM_EMAIL_HOST_PASSWORD = 'abcdefg' <br>
SUPPORT_EMAIL_HOST_USER = 'xyz@example.com' <br>
SUPPORT_EMAIL_HOST_PASSWORD = 'abczqwert' <br>
EMAIL_IMAP_HOST = 'imap.gmail.com' <br>
EMAIL_IMAP_PORT = 993 <br>
DEFAULT_SITE_SCHEME='http' <br>
DEFAULT_SITE_DOMAIN='localhost:8000' <br>
