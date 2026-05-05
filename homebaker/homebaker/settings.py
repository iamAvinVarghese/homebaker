"""
Django settings for homebaker project.
"""

import os
from pathlib import Path
from decouple import config

# =====================================
# BASE DIRECTORY
# =====================================
BASE_DIR = Path(__file__).resolve().parent.parent


# =====================================
# SECURITY
# =====================================
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-this')

DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = []

# CSRF Trusted Origins for local development
CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:8000',
    'http://localhost:8000',
]


# =====================================
# APPLICATIONS
# =====================================
INSTALLED_APPS = [
    # 'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Local apps
    'main',
    'chatbot',
]


# =====================================
# MIDDLEWARE
# =====================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# =====================================
# URL CONFIG
# =====================================
ROOT_URLCONF = 'homebaker.urls'


# =====================================
# TEMPLATES
# =====================================
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
                'main.context_processors.notification_count',
            ],
        },
    },
]


# =====================================
# WSGI
# =====================================
WSGI_APPLICATION = 'homebaker.wsgi.application'


# =====================================
# DATABASE
# =====================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'homebaker_db',
        'USER': 'postgres',
        'PASSWORD': 'avin123',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}


# =====================================
# PASSWORD VALIDATION
# =====================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# =====================================
# INTERNATIONALIZATION
# =====================================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True


# =====================================
# STATIC FILES
# =====================================
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']


# =====================================
# MEDIA FILES
# =====================================
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# =====================================
# DEFAULT PRIMARY KEY
# =====================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# =====================================
# EMAIL CONFIGURATION (Gmail SMTP)
# =====================================

EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default=EMAIL_HOST_USER or 'noreply@homebaker.com')

if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
else:
    # Fallback for development (prints emails to terminal)
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


# =====================================
# OTP SETTINGS
# =====================================
OTP_EXPIRY_MINUTES = 5
OTP_LENGTH = 6


# =====================================
# AI CONFIGURATION
# =====================================
GEMINI_API_KEY = config('GEMINI_API_KEY', default='')
LEONARDO_API_KEY = config('LEONARDO_API_KEY', default='')


# =====================================
# LOGGING
# =====================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
# =====================================
# AUTHENTICATION REDIRECTS
# =====================================
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
