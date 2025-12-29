import os
from pathlib import Path
from dotenv import load_dotenv
from celery.schedules import crontab

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

allowed_hosts_env = os.getenv('DJANGO_ALLOWED_HOSTS')
ALLOWED_HOSTS = [host.strip() for host in allowed_hosts_env.split(',')]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'tickets',
    'widget_tweaks',
    'account', 
    'ai',
    'dashboard',
    'servicenow',
    'background_task',
    'django_celery_results',
    'django_celery_beat',
]   

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'AI_Powered_IT_Ticket_System.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR.joinpath('templates')
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'AI_Powered_IT_Ticket_System.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/
# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Authentication Redirects
LOGIN_URL = '/account/login/'
LOGOUT_REDIRECT_URL = '/account/login/'
LOGIN_REDIRECT_URL = '/'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Logging Configuration
LOG_DIR = os.path.join(BASE_DIR, 'logs')
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'app.log'),
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        '': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# Authentication Redirects
LOGIN_URL = '/account/login/'
LOGOUT_REDIRECT_URL = '/account/login/'
LOGIN_REDIRECT_URL = '/'

# Email Backend Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_HOST = os.getenv('EMAIL_SMTP_HOST')
EMAIL_PORT = os.getenv('EMAIL_SMTP_PORT')
EMAIL_ACCOUNTS = {
    "system": {
        "EMAIL_HOST_USER": os.getenv('SYSTEM_EMAIL_HOST_USER'),
        "EMAIL_HOST_PASSWORD": os.getenv('SYSTEM_EMAIL_HOST_PASSWORD'),
    },
    "support": {
        "EMAIL_HOST_USER": os.getenv('SUPPORT_EMAIL_HOST_USER'),
        "EMAIL_HOST_PASSWORD": os.getenv('SUPPORT_EMAIL_HOST_PASSWORD'),
    }
}

EMAIL_IMAP_HOST = os.getenv('EMAIL_IMAP_HOST')
EMAIL_IMAP_PORT = os.getenv('EMAIL_IMAP_PORT')

# Site Configuration
DEFAULT_SITE_SCHEME=os.getenv('DEFAULT_SITE_SCHEME','http')
DEFAULT_SITE_DOMAIN=os.getenv('DEFAULT_SITE_DOMAIN')

# ServiceNow Configuration
SERVICENOW_INSTANCE = os.getenv('SERVICENOW_INSTANCE')
SERVICENOW_USERNAME = os.getenv('SERVICENOW_USERNAME')
SERVICENOW_PASSWORD = os.getenv('SERVICENOW_PASSWORD')
SERVICENOW_SYSID = os.getenv('SERVICENOW_SYSID')


CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_BACKEND = 'django-db'
CELERY_TIMEZONE = TIME_ZONE


CELERY_BEAT_SCHEDULE = {
    "sync-servicenow-ticket-status-every-10-min": {
        "task": "servicenow.utils.task.sync_servicenow_ticket_statuses",
        "schedule": crontab(minute="*/10"),  # every 10 minutes
    },
    "retry-servicenow-ticket-creation-every-10-min": {
        "task": "servicenow.utils.task.servicenow_ticket_retry",
        "schedule": crontab(minute="*/10"),  # every 10 minutes
    },
    "check-email-replay-status-every-10-min": {
        "task": "tickets.utils.task.send_email_replay_with_ticket",
        "schedule": crontab(minute="*/5"),  # every 10 minutes
    },
}