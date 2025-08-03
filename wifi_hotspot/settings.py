# settings.py

import os
from pathlib import Path
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = os.environ.get('SECRET_KEY')

# Use Render's environment variable for the external hostname
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')

# Set allowed hosts and trusted origins
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# IMPORTANT: You need to add your Render URL here
# For example: https://your-app-name.onrender.com
# This is crucial for CSRF protection on production.
CSRF_TRUSTED_ORIGINS = [f'https://{RENDER_EXTERNAL_HOSTNAME}'] if RENDER_EXTERNAL_HOSTNAME else []

INSTALLED_APPS = [
    # Jazzmin must be listed BEFORE django.contrib.admin
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise must be listed after SecurityMiddleware
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
        'DIRS': [BASE_DIR / 'templates'],
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

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

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

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Africa/Kampala'

USE_I18N = True

USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

MIKROTIK_HOST = os.environ.get('MIKROTIK_HOST')
MIKROTIK_USER = os.environ.get('MIKROTIK_USER')
MIKROTIK_PASSWORD = os.environ.get('MIKROTIK_PASSWORD')

# =========================================================
# JAZZMIN ADMIN PANEL CONFIGURATION
# =========================================================

JAZZMIN_SETTINGS = {
    # TITLE AND BRANDING
    "site_title": "WiFi Hotspot Admin",
    "site_header": "WiFi Hotspot",
    "site_brand": "Hotspot",
    "site_logo": None,
    "login_logo": None,
    "login_logo_dark": None,
    "site_icon": None,
    "welcome_sign": "Welcome to the WiFi Hotspot Admin Panel",

    # UI/VISUAL STYLES
    "changeform_format": "horizontal",
    "changeform_format_overrides": {"core.plan": "vertical", "core.wifisession": "vertical"},
    "theme": "united", # Examples: "darkly", "cosmo", "united", "minty"
    "navbar": "navbar-dark navbar-primary",
    "accent": "accent-info",
    "topbar_links": True,

    # MENU AND NAVIGATION
    "show_sidebar": True,
    "sidebar_fixed": True,
    "sidebar_nav_child_indent": True,
    "navigation_expanded": True,
    "hide_apps": [],
    "order_with_respect_to": ["core", "auth"],
    "menu": [
        {
            "app": "core",
            "name": "WiFi Management",
            "icon": "fas fa-wifi",
            "models": [
                {"model": "core.Plan"},
                {"model": "core.WifiSession"},
            ]
        },
        {"app": "auth", "name": "Users & Permissions"},
    ]
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-primary",
    "accent": "accent-primary",
    "navbar": "navbar-primary navbar-dark",
    "no_navbar_reference": False,
    "sidebar_nav_small_text": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": True,
    "sidebar_nav_flat_style": True,
    "sidebar_nav_fixed_style": True,
}