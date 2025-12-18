"""
Django settings for WP_Pro-FM project.
"""

import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DJANGO_DEBUG', 'True').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Application definition
INSTALLED_APPS = [
    # Unfold admin theme (must be before django.contrib.admin)
    'unfold',
    'unfold.contrib.filters',
    'unfold.contrib.forms',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party apps
    'rest_framework',
    'corsheaders',
    'django_celery_beat',
    'django_celery_results',

    # Local apps
    'apps.media',
    'apps.content',
    'apps.seo',
    'apps.email_marketing',
    'apps.front_page',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

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

WSGI_APPLICATION = 'config.wsgi.application'

# Database - PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB', 'wp_profm'),
        'USER': os.environ.get('POSTGRES_USER', 'postgres'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'postgres'),
        'HOST': os.environ.get('POSTGRES_HOST', 'db'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
    }
}

# WordPress Database (read-only for syncing)
WP_DATABASE = {
    'ENGINE': 'django.db.backends.mysql',
    'NAME': os.environ.get('WP_DB_NAME', ''),
    'USER': os.environ.get('WP_DB_USER', ''),
    'PASSWORD': os.environ.get('WP_DB_PASSWORD', ''),
    'HOST': os.environ.get('WP_DB_HOST', ''),
    'PORT': os.environ.get('WP_DB_PORT', '3306'),
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'de-de'
TIME_ZONE = 'Europe/Berlin'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# CORS
CORS_ALLOWED_ORIGINS = os.environ.get(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:3000,http://127.0.0.1:3000'
).split(',')

# Celery Configuration
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/0')
CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'django-cache'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# WordPress API Configuration
WP_SITE_URL = os.environ.get('WP_SITE_URL', '')
WP_USERNAME = os.environ.get('WP_USERNAME', '')
WP_APP_PASSWORD = os.environ.get('WP_APP_PASSWORD', '')

# OpenAI Configuration
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@profm24.de')

# Logging
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
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.environ.get('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
    },
}

# Unfold Admin Configuration
from django.templatetags.static import static
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

UNFOLD = {
    "SITE_TITLE": "Pro-FM Admin",
    "SITE_HEADER": "Pro-FM Management",
    "SITE_SUBHEADER": "Facility Management Content & Marketing Platform",
    "SITE_URL": "/",
    "SITE_SYMBOL": "corporate_fare",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "ENVIRONMENT": "config.settings.environment_callback",
    "DASHBOARD_CALLBACK": "apps.content.admin.dashboard_callback",
    "COLORS": {
        "primary": {
            "50": "250 245 255",
            "100": "243 232 255",
            "200": "233 213 255",
            "300": "216 180 254",
            "400": "192 132 252",
            "500": "59 130 246",
            "600": "37 99 235",
            "700": "29 78 216",
            "800": "30 64 175",
            "900": "30 58 138",
            "950": "23 37 84",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": _("Dashboard"),
                "separator": True,
                "collapsible": False,
                "items": [
                    {
                        "title": _("Dashboard"),
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                    },
                ],
            },
            {
                "title": _("Content Management"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Posts"),
                        "icon": "article",
                        "link": reverse_lazy("admin:content_post_changelist"),
                        "badge": "apps.content.admin.get_pending_posts_count",
                    },
                    {
                        "title": _("Categories"),
                        "icon": "category",
                        "link": reverse_lazy("admin:content_category_changelist"),
                    },
                    {
                        "title": _("Tags"),
                        "icon": "label",
                        "link": reverse_lazy("admin:content_tag_changelist"),
                    },
                    {
                        "title": _("Content Templates"),
                        "icon": "description",
                        "link": reverse_lazy("admin:content_contenttemplate_changelist"),
                    },
                    {
                        "title": _("Generation Jobs"),
                        "icon": "smart_toy",
                        "link": reverse_lazy("admin:content_contentgenerationjob_changelist"),
                    },
                ],
            },
            {
                "title": _("Front Page"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Sliders"),
                        "icon": "slideshow",
                        "link": reverse_lazy("admin:front_page_sliderrevolution_changelist"),
                    },
                    {
                        "title": _("Slides"),
                        "icon": "image",
                        "link": reverse_lazy("admin:front_page_slide_changelist"),
                    },
                    {
                        "title": _("Homepage Sections"),
                        "icon": "view_module",
                        "link": reverse_lazy("admin:front_page_homepagesection_changelist"),
                    },
                    {
                        "title": _("Front Page Settings"),
                        "icon": "settings",
                        "link": reverse_lazy("admin:front_page_frontpagesettings_changelist"),
                    },
                ],
            },
            {
                "title": _("Media Library"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Media Files"),
                        "icon": "perm_media",
                        "link": reverse_lazy("admin:media_mediafile_changelist"),
                    },
                    {
                        "title": _("Collections"),
                        "icon": "collections",
                        "link": reverse_lazy("admin:media_mediacollection_changelist"),
                    },
                    {
                        "title": _("Sync Logs"),
                        "icon": "sync",
                        "link": reverse_lazy("admin:media_mediasynclog_changelist"),
                    },
                ],
            },
            {
                "title": _("SEO & Analytics"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Keywords"),
                        "icon": "search",
                        "link": reverse_lazy("admin:seo_keyword_changelist"),
                    },
                    {
                        "title": _("Ranking History"),
                        "icon": "trending_up",
                        "link": reverse_lazy("admin:seo_keywordrankinghistory_changelist"),
                    },
                    {
                        "title": _("Site Audits"),
                        "icon": "fact_check",
                        "link": reverse_lazy("admin:seo_siteaudit_changelist"),
                    },
                    {
                        "title": _("Audit Issues"),
                        "icon": "warning",
                        "link": reverse_lazy("admin:seo_siteauditissue_changelist"),
                    },
                    {
                        "title": _("Backlinks"),
                        "icon": "link",
                        "link": reverse_lazy("admin:seo_backlink_changelist"),
                    },
                    {
                        "title": _("IndexNow"),
                        "icon": "public",
                        "link": reverse_lazy("admin:seo_indexnowsubmission_changelist"),
                    },
                ],
            },
            {
                "title": _("Email Marketing"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Subscribers"),
                        "icon": "people",
                        "link": reverse_lazy("admin:email_marketing_subscriber_changelist"),
                    },
                    {
                        "title": _("Mailing Lists"),
                        "icon": "list",
                        "link": reverse_lazy("admin:email_marketing_mailinglist_changelist"),
                    },
                    {
                        "title": _("Campaigns"),
                        "icon": "campaign",
                        "link": reverse_lazy("admin:email_marketing_campaign_changelist"),
                    },
                    {
                        "title": _("Email Templates"),
                        "icon": "email",
                        "link": reverse_lazy("admin:email_marketing_emailtemplate_changelist"),
                    },
                    {
                        "title": _("Automations"),
                        "icon": "auto_mode",
                        "link": reverse_lazy("admin:email_marketing_automationworkflow_changelist"),
                    },
                ],
            },
            {
                "title": _("System"),
                "separator": True,
                "collapsible": True,
                "items": [
                    {
                        "title": _("Users"),
                        "icon": "person",
                        "link": reverse_lazy("admin:auth_user_changelist"),
                    },
                    {
                        "title": _("Groups"),
                        "icon": "group",
                        "link": reverse_lazy("admin:auth_group_changelist"),
                    },
                    {
                        "title": _("Celery Tasks"),
                        "icon": "schedule",
                        "link": reverse_lazy("admin:django_celery_beat_periodictask_changelist"),
                    },
                    {
                        "title": _("Task Results"),
                        "icon": "task",
                        "link": reverse_lazy("admin:django_celery_results_taskresult_changelist"),
                    },
                ],
            },
        ],
    },
}


def environment_callback(request):
    """Return environment badge for admin header."""
    if DEBUG:
        return ["Development", "warning"]
    return ["Production", "success"]
