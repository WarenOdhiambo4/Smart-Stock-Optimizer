"""
Django settings for saas_project project.
"""

import os
from pathlib import Path

from decouple import config
import dj_database_url

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-dev-key-change-in-production')

DEBUG = config('DEBUG', default='False').lower() == 'true'

ALLOWED_HOSTS = ['*']
if not DEBUG:
    ALLOWED_HOSTS = ['.onrender.com', 'localhost', '127.0.0.1']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party apps
    'rest_framework',
    'django_filters',
    'corsheaders',
    'django_extensions',
    'simple_history',
    # Local apps
    'core.apps.CoreConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
]

ROOT_URLCONF = 'saas_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.system_content',
            ],
        },
    },
]

WSGI_APPLICATION = 'saas_project.wsgi.application'

# Database Configuration
DATABASE_URL = config('DATABASE_URL', default='')
DATABASE_HOST = config('DATABASE_HOST', default=config('DB_HOST', default=''))

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            ssl_require=True
        )
    }
elif DATABASE_HOST:
    db_password = config("DATABASE_PASSWORD", default=config("DB_PASSWORD", default=""))
    if isinstance(db_password, str):
        db_password = db_password.strip()
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": config("DATABASE_NAME", default=config("DB_NAME", default="postgres")),
            "USER": config("DATABASE_USER", default=config("DB_USER", default="")),
            "PASSWORD": db_password,
            "HOST": DATABASE_HOST,
            "PORT": config("DATABASE_PORT", default=config("DB_PORT", default="5432")),
            "OPTIONS": {"sslmode": "require"},
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

X_FRAME_OPTIONS = 'ALLOWALL'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '[{asctime}] {levelname} {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'

# Session Configuration - 30 minute timeout for security
SESSION_COOKIE_AGE = 1800  # 30 minutes (30 * 60 seconds)
SESSION_SAVE_EVERY_REQUEST = False  # Don't refresh session on every request
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # Expire session when browser closes

# Email Configuration for 2FA
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='kabisaerp@gmail.com')

# Supabase Configuration (using environment variables)
SUPABASE_URL = config('SUPABASE_URL', default='')
SUPABASE_ANON_KEY = config('SUPABASE_ANON_KEY', default='')

# Accounting system defaults (used for ledger postings)
ACCOUNTING_DEFAULT_CASH_ACCOUNT_CODE = config('ACCOUNTING_DEFAULT_CASH_ACCOUNT_CODE', default='1000')
ACCOUNTING_DEFAULT_CASH_ACCOUNT_NAME = config('ACCOUNTING_DEFAULT_CASH_ACCOUNT_NAME', default='Cash on Hand')
ACCOUNTING_DEFAULT_BANK_ACCOUNT_CODE = config('ACCOUNTING_DEFAULT_BANK_ACCOUNT_CODE', default='1010')
ACCOUNTING_DEFAULT_BANK_ACCOUNT_NAME = config('ACCOUNTING_DEFAULT_BANK_ACCOUNT_NAME', default='Bank Account')
ACCOUNTING_DEFAULT_MOBILE_ACCOUNT_CODE = config('ACCOUNTING_DEFAULT_MOBILE_ACCOUNT_CODE', default='1020')
ACCOUNTING_DEFAULT_MOBILE_ACCOUNT_NAME = config('ACCOUNTING_DEFAULT_MOBILE_ACCOUNT_NAME', default='Mobile Money')
ACCOUNTING_DEFAULT_CARD_ACCOUNT_CODE = config('ACCOUNTING_DEFAULT_CARD_ACCOUNT_CODE', default='1030')
ACCOUNTING_DEFAULT_CARD_ACCOUNT_NAME = config('ACCOUNTING_DEFAULT_CARD_ACCOUNT_NAME', default='Card Receipts')
ACCOUNTING_DEFAULT_OTHER_ACCOUNT_CODE = config('ACCOUNTING_DEFAULT_OTHER_ACCOUNT_CODE', default='1099')
ACCOUNTING_DEFAULT_OTHER_ACCOUNT_NAME = config('ACCOUNTING_DEFAULT_OTHER_ACCOUNT_NAME', default='Undeposited Funds')
ACCOUNTING_DEFAULT_PAYROLL_EXPENSE_CODE = config('ACCOUNTING_DEFAULT_PAYROLL_EXPENSE_CODE', default='5000')
ACCOUNTING_DEFAULT_PAYROLL_EXPENSE_NAME = config('ACCOUNTING_DEFAULT_PAYROLL_EXPENSE_NAME', default='Payroll Expense')
ACCOUNTING_DEFAULT_LOAN_FUNDING_CODE = config('ACCOUNTING_DEFAULT_LOAN_FUNDING_CODE', default='1010')
ACCOUNTING_DEFAULT_LOAN_FUNDING_NAME = config('ACCOUNTING_DEFAULT_LOAN_FUNDING_NAME', default='Bank Account')
ACCOUNTING_DEFAULT_REVENUE_ACCOUNT_CODE = config('ACCOUNTING_DEFAULT_REVENUE_ACCOUNT_CODE', default='4000')
ACCOUNTING_DEFAULT_REVENUE_ACCOUNT_NAME = config('ACCOUNTING_DEFAULT_REVENUE_ACCOUNT_NAME', default='Sales Revenue')
ACCOUNTING_DEFAULT_EXPENSE_ACCOUNT_CODE = config('ACCOUNTING_DEFAULT_EXPENSE_ACCOUNT_CODE', default='6000')
ACCOUNTING_DEFAULT_EXPENSE_ACCOUNT_NAME = config('ACCOUNTING_DEFAULT_EXPENSE_ACCOUNT_NAME', default='Operating Expense')

# Finance module controls
ACCOUNTING_AUTO_POST_FROM_CORE = config('ACCOUNTING_AUTO_POST_FROM_CORE', default=True, cast=bool)
ACCOUNTING_MANUAL_INCOME_REGISTER = config('ACCOUNTING_MANUAL_INCOME_REGISTER', default=False, cast=bool)
ACCOUNTING_MANUAL_EXPENSE_REGISTER = config('ACCOUNTING_MANUAL_EXPENSE_REGISTER', default=False, cast=bool)
ACCOUNTING_MANUAL_PAYROLL_LEDGER = config('ACCOUNTING_MANUAL_PAYROLL_LEDGER', default=False, cast=bool)

# REST Framework Configuration - Enterprise Grade
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
}

# CORS Configuration for React Frontend
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Google Maps API Configuration
GOOGLE_MAPS_API_KEY = config('GOOGLE_MAPS_API_KEY', default='')

# Celery Configuration for Background Tasks
CELERY_BROKER_URL = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
