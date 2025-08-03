# learnflow_ai/django_backend/django_backend/settings.py

import os
from pathlib import Path
import json
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
# It's highly recommended to set this as an environment variable on Render
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-@e^$b!q#^1234567890abcdefghijklmnopqrstuvwxyz')

# SECURITY WARNING: don't run with debug turned on in production!
# Set this as an environment variable on Render (True for temporary debugging, False for production)
DEBUG = os.environ.get("DEBUG", "False") == "True"

ALLOWED_HOSTS = ['*']

# Application definition

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'wifi_hotspot.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'wifi_hotspot.wsgi.application'

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases
if os.environ.get('DATABASE_URL'):
    # Use the database URL from the environment variable (e.g., on Render)
    DATABASES = {
        'default': dj_database_url.config(default=os.environ.get('DATABASE_URL'))
    }
else:
    # Fallback to a local SQLite database for development
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Africa's Talking API Credentials
AFRICASTALKING_API_KEY = os.environ.get('AFRICASTALKING_API_KEY')
AFRICASTALKING_USERNAME = os.environ.get('AFRICASTALKING_USERNAME')
AFRICASTALKING_SENDER_ID = os.environ.get('AFRICASTALKING_SENDER_ID')

# JAZZMIN Settings
JAZZMIN_SETTINGS = {
    "site_title": "MoMo WiFi Admin",
    "site_header": "MoMo WiFi",
    "site_brand": "MoMo WiFi",
    "site_icon": "images/logo.png",
    # Welcome message
    "welcome_sign": "Welcome to the MoMo WiFi Admin Panel",
    # Copyright on the footer
    "copyright": "MoMo WiFi Ltd",
}