"""
Django 5 settings for WBEE Universal Company Manager
Production-ready configuration with environment variables
"""

import os
from pathlib import Path
from decouple import config, Csv
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ==============================================================================
# CORE SETTINGS
# ==============================================================================

# Security
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='', cast=Csv())

# Google Maps API key
GOOGLE_MAPS_API_KEY = config('GOOGLE_MAPS_API_KEY', default='')

# Application definition
DJANGO_APPS = [
    'grappelli',  # Must be before django.contrib.admin
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.humanize',
    'django.contrib.sitemaps',
]

THIRD_PARTY_APPS = [
    'django_extensions',
    'easy_thumbnails',
    'filer',
    'mptt',
    'corsheaders',  # For API access
    'rest_framework',  # For API endpoints
    'django_filters',  # For advanced filtering
    'import_export',  # For data import/export
    'crispy_forms',  # For better forms
    'crispy_bootstrap5',  # Bootstrap 5 support
    'widget_tweaks',  # Form rendering utilities
]

LOCAL_APPS = [
    'asset.apps.AssetConfig',
    'client.apps.ClientConfig',
    'company.apps.CompanyConfig',  # New company management app
    'home.apps.HomeConfig',
    #'helpdesk.apps.HelpdeskConfig',
    'hr.apps.HrConfig',
    'location.apps.LocationConfig',
    'project.apps.ProjectConfig',
    'receipts.apps.ReceiptsConfig',
    'material.apps.MaterialConfig',
    'schedule.apps.ScheduleConfig',
    'timecard.apps.TimecardConfig',
    'todo',
    'wip.apps.WipConfig',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ==============================================================================
# MIDDLEWARE
# ==============================================================================

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # For static files in production
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
]

# ==============================================================================
# URLS AND WSGI
# ==============================================================================

ROOT_URLCONF = 'wbee.urls'
WSGI_APPLICATION = 'wbee.wsgi.application'

# ==============================================================================
# TEMPLATES
# ==============================================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'wbee.context_processors.site_title.site_title',
            ],
        },
    },
]

# ==============================================================================
# DATABASES
# ==============================================================================

#DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.postgresql',
#        'NAME': config('DATABASE_NAME', default='workerbee_db'),
#        'USER': config('DATABASE_USER', default='workerbee'),
#        'PASSWORD': config('DATABASE_PASSWORD', default='workerbee_secure_password_2025'),
#        'HOST': config('DATABASE_HOST', default='localhost'),
#        'PORT': config('DATABASE_PORT', default='5432'),
#        'CONN_MAX_AGE': 600,
#    }
#}
DATABASES = {
    'default': dj_database_url.config()
}

import sys
if 'pytest' in sys.argv[0]:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }

# ==============================================================================
# AUTHENTICATION
# ==============================================================================

AUTH_USER_MODEL = 'hr.Worker'
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8},
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
LOGIN_URL = '/admin/login/'

# ==============================================================================
# INTERNATIONALIZATION
# ==============================================================================

LANGUAGE_CODE = 'en-us'
TIME_ZONE = config('TIME_ZONE', default='America/Phoenix')  # Arizona/MST
USE_I18N = True
USE_L10N = True
USE_TZ = True

# ==============================================================================
# STATIC AND MEDIA FILES
# ==============================================================================

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Static files storage
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ==============================================================================
# DEFAULT AUTO FIELD
# ==============================================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==============================================================================
# SITE FRAMEWORK
# ==============================================================================

SITE_ID = 1

# ==============================================================================
# EMAIL CONFIGURATION
# ==============================================================================

EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='localhost')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_USE_SSL = config('EMAIL_USE_SSL', default=False, cast=bool)
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@wbee.app')
SERVER_EMAIL = config('SERVER_EMAIL', default='server@wbee.app')

# Receipt notification settings
RECEIPT_NOTIFICATION_EMAIL = config('RECEIPT_NOTIFICATION_EMAIL', default='admin@wbee.app')
SEND_REIMBURSEMENT_NOTIFICATIONS = config('SEND_REIMBURSEMENT_NOTIFICATIONS', default=True, cast=bool)

# ==============================================================================
# SECURITY SETTINGS
# ==============================================================================

if not DEBUG:
    # HTTPS Settings
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # Cookie Security
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = True
    
    # Security Headers
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'
    
    # Referrer Policy
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# ==============================================================================
# CORS SETTINGS (for API access)
# ==============================================================================

CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', default='https://wbee.app', cast=Csv())
CORS_ALLOW_CREDENTIALS = True

# ==============================================================================
# REST FRAMEWORK (API Configuration)
# ==============================================================================

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

# ==============================================================================
# THIRD PARTY APP SETTINGS
# ==============================================================================

# Grappelli
GRAPPELLI_ADMIN_TITLE = 'WBEE Universal Company Manager for the Brick Box Bros'

# Easy Thumbnails
THUMBNAIL_HIGH_RESOLUTION = True
THUMBNAIL_PROCESSORS = (
    'easy_thumbnails.processors.colorspace',
    'easy_thumbnails.processors.autocrop',
    'filer.thumbnail_processors.scale_and_crop_with_subject_location',
    'easy_thumbnails.processors.filters',
)

# Filer
FILER_ENABLE_LOGGING = True
FILER_DEBUG = DEBUG

# Graph Models
GRAPH_MODELS = {
    'all_applications': True,
    'group_models': True,
}

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

# ==============================================================================
# TODO APP SETTINGS
# ==============================================================================

TODO_STAFF_ONLY = config('TODO_STAFF_ONLY', default=False, cast=bool)
TODO_DEFAULT_ASSIGNEE = config('TODO_DEFAULT_ASSIGNEE', default='admin')
TODO_DEFAULT_LIST_SLUG = config('TODO_DEFAULT_LIST_SLUG', default='tickets')
TODO_PUBLIC_SUBMIT_REDIRECT = config('TODO_PUBLIC_SUBMIT_REDIRECT', default='home:dashboard')

# ==============================================================================
# LOGGING - ROBUST CONFIGURATION
# ==============================================================================

# Ensure logs directory exists
import os
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'django2.log',
            'maxBytes': 1024*1024*5,  # 5MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': config('DJANGO_LOG_LEVEL', default='INFO'),
            'propagate': True,
        },
        'receipts': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        # Add your app loggers here
        'wbee': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# ==============================================================================
# CACHING
# ==============================================================================

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://127.0.0.1:6379/1'),
        'KEY_PREFIX': 'wbee',
        'TIMEOUT': 300,
    } if config('REDIS_URL', default=None) else {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Session engine
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# ==============================================================================
# PERFORMANCE SETTINGS
# ==============================================================================

# Database connection pooling
#if 'postgresql' in DATABASES['default']['ENGINE']:
#    DATABASES['default']['OPTIONS'] = {
#        'MAX_CONNS': 20,
#       'MIN_CONNS': 5,
#    }

# ==============================================================================
# DEVELOPMENT SETTINGS
# ==============================================================================

if DEBUG:
    # Add development-specific settings
    INTERNAL_IPS = ['127.0.0.1', '::1']
    
    # Add django-debug-toolbar if available
    try:
        import debug_toolbar
        INSTALLED_APPS += ['debug_toolbar']
        MIDDLEWARE.insert(1, 'debug_toolbar.middleware.DebugToolbarMiddleware')
    except ImportError:
        pass

# ==============================================================================
# CUSTOM COMPANY SETTINGS
# ==============================================================================

# Company-specific configurations
COMPANY_NAME = config('COMPANY_NAME', default='WBEE Universal Company')
SITE_TITLE = config('SITE_TITLE', default='WBEE Universal Company Manager')
COMPANY_ADDRESS = config('COMPANY_ADDRESS', default='')
COMPANY_PHONE = config('COMPANY_PHONE', default='')
COMPANY_EMAIL = config('COMPANY_EMAIL', default='info@wbee.app')
COMPANY_WEBSITE = config('COMPANY_WEBSITE', default='https://wbee.app')

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

# ==============================================================================
# ENVIRONMENT-SPECIFIC OVERRIDES
# ==============================================================================

# Load environment-specific settings
environment = config('ENVIRONMENT', default='development')

# Asset Management Settings
ASSET_NOTIFICATION_EMAIL = 'admin@yourdomain.com'  # Replace with your email
ASSET_DEPRECIATION_ENABLED = True

# Media files warning is expected in DEBUG mode
# In production, you'll configure nginx/apache to serve media files

