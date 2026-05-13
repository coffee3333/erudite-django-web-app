"""
Django settings for config project.
"""

from pathlib import Path
from datetime import timedelta
import os

from decouple import config  # pip install python-decouple

# ──────────────────────────────────────
# Core paths
# ──────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent


# ──────────────────────────────────────
# Security
# ──────────────────────────────────────
SECRET_KEY = config("DJANGO_SECRET_KEY", default="change-me-in-prod")
DEBUG = config("DEBUG", default=True, cast=bool)

_allowed = config("ALLOWED_HOSTS", default="")
ALLOWED_HOSTS = [h for h in _allowed.split(",") if h] or ["localhost", "127.0.0.1", "[::1]"]

# HTTPS / proxy (needed on Heroku / Render behind reverse-proxy)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE = not DEBUG
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS",
    default="http://localhost:3000",
).split(",")

# ──────────────────────────────────────
# CORS
# ──────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# ──────────────────────────────────────
# Applications
# ──────────────────────────────────────
INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "allauth",
    # Third-party
    'behave_django',  # <- cucumber / BDD
    "corsheaders",
    "drf_yasg",
    "django_filters",
    "rest_framework",
    "rest_framework.authtoken",  # keep if you need browsable API token auth
    "rest_framework_simplejwt.token_blacklist",
    # Cloudinary
    "cloudinary",
    "cloudinary_storage",
    # Auth / social
    "social_django",
    # Local apps
    "authentication",
    "core",
    "django_extensions",
    # Celery results
    "django_celery_results",
    # LTI 1.3
    "lti",
]

SITE_ID = 1

# ──────────────────────────────────────
# Middleware
# ──────────────────────────────────────
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "social_django.middleware.SocialAuthExceptionMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# ──────────────────────────────────────
# URLs / WSGI
# ──────────────────────────────────────
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

# ──────────────────────────────────────
# Templates
# ──────────────────────────────────────
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ──────────────────────────────────────
# Database
# ──────────────────────────────────────
if not DEBUG:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME'),
            'USER': os.environ.get('DB_USER'),
            'PASSWORD': os.environ.get('DB_PASSWORD'),
            'HOST': os.environ.get('DB_HOST'),
            'PORT': os.environ.get('DB_PORT', 5432),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
# ──────────────────────────────────────
# Password validation
# ──────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ──────────────────────────────────────
# Internationalisation
# ──────────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ──────────────────────────────────────
# Static & media
# ──────────────────────────────────────

STATIC_URL = 'api/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'mediafiles'

# Cloudinary
CLOUDINARY_STORAGE = {
    "CLOUD_NAME": config("CLOUDINARY_CLOUD_NAME", default=""),
    "API_KEY": config("CLOUDINARY_API_KEY", default=""),
    "API_SECRET": config("CLOUDINARY_API_SECRET", default=""),
}

STORAGES = {
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# ──────────────────────────────────────
# Custom user
# ──────────────────────────────────────
AUTH_USER_MODEL = "authentication.User"

# ──────────────────────────────────────
# Email (Gmail SMTP)
# ──────────────────────────────────────
EMAIL_BACKEND = config("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# ──────────────────────────────────────
# REST Framework
# ──────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "600/hour" if not DEBUG else "9999/hour",
        "user": "3000/hour" if not DEBUG else "9999/hour",
    },
    "DATETIME_FORMAT": "%d.%m.%Y %H:%M",
    "DATE_FORMAT": "%d.%m.%Y",
    "TIME_FORMAT": "%H:%M",
}

# ──────────────────────────────────────
# Simple JWT
# ──────────────────────────────────────
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ALGORITHM": "HS256",
    "UPDATE_LAST_LOGIN": True,
}

# ──────────────────────────────────────
# dj-rest-auth
# ──────────────────────────────────────
REST_USE_JWT = True
DJANGO_REST_AUTH = {
    "JWT_AUTH_COOKIE": "access",
    "JWT_AUTH_REFRESH_COOKIE": "refresh",
}


# ──────────────────────────────────────
# Swagger / drf-yasg
# ──────────────────────────────────────
SWAGGER_SETTINGS = {
    "SECURITY_DEFINITIONS": {
        "Bearer": {"type": "apiKey", "name": "Authorization", "in": "header"}
    }
}

# ──────────────────────────────────────
# Social authentication
# ──────────────────────────────────────

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY    = config("GOOGLE_CLIENT_ID", default="")
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = config("GOOGLE_CLIENT_SECRET", default="")

AUTHENTICATION_BACKENDS = (
    "social_core.backends.google.GoogleOAuth2",
    "django.contrib.auth.backends.ModelBackend",
)

SOCIAL_AUTH_PIPELINE = (
    "social_core.pipeline.social_auth.social_details",
    "social_core.pipeline.social_auth.social_uid",
    "social_core.pipeline.social_auth.auth_allowed",
    "social_core.pipeline.social_auth.social_user",
    "social_core.pipeline.social_auth.associate_by_email",
    "social_core.pipeline.user.get_username",
    "social_core.pipeline.user.create_user",
    "social_core.pipeline.social_auth.associate_user",
    "social_core.pipeline.social_auth.load_extra_data",
    "social_core.pipeline.user.user_details",
)

SOCIAL_AUTH_ALLOW_NEW_USER = False

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ──────────────────────────────────────
# Celery
# ──────────────────────────────────────
REDIS_URL = config("REDIS_URL", default="redis://localhost:6379/0")

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = "django-db"
CELERY_CACHE_BACKEND = "django-cache"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }
}

# ──────────────────────────────────────
# LTI
# ──────────────────────────────────────
FRONTEND_URL = config("FRONTEND_URL", default="http://localhost:5173")

# Rewrite public-facing LTI platform URLs to internal Docker IPs
# Key = what's stored in the DB, Value = internal reachable URL
LTI_HOST_REWRITES = {
    "http://localhost:8060": "http://172.20.0.6",
    "https://localhost:8060": "http://172.20.0.6",
}
