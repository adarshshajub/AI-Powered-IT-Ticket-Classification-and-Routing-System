# 🧠 AI-Powered IT Ticket Automation System

## An intelligent IT support automation platform that uses Machine Learning, NLP, and GenAI-assisted semantic embeddings to analyze user-reported issues (via web or email), automatically classify ticket categories and priorities, and integrate with ServiceNow for incident creation and routing.


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
