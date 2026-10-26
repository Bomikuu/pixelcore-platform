"""Django settings for the PixelCore business platform."""

from datetime import timedelta
from pathlib import Path
import os
import sys


BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default=False):
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DEBUG = env_bool("DJANGO_DEBUG", False)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "businesses",
    "catalog",
    "content",
    "commerce",
    "scheduling",
    "operations",
    "workforce",
    "displays",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "pixelcore_backend.urls"
WSGI_APPLICATION = "pixelcore_backend.wsgi.application"
ASGI_APPLICATION = "pixelcore_backend.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

database_engine = os.getenv("DJANGO_DB_ENGINE", "postgresql")
if database_engine == "sqlite":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DJANGO_DB_NAME", "pixelcore"),
            "USER": os.getenv("DJANGO_DB_USER", "pixelcore"),
            "PASSWORD": os.environ["DJANGO_DB_PASSWORD"],
            "HOST": os.getenv("DJANGO_DB_HOST", "db"),
            "PORT": int(os.getenv("DJANGO_DB_PORT", "5432")),
            "CONN_MAX_AGE": 30,
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "EXCEPTION_HANDLER": "pixelcore_backend.exceptions.api_exception_handler",
    "DEFAULT_THROTTLE_RATES": {
        "anon": "60/hour",
        "user": "1000/hour",
        "auth": "10/minute",
        "identity_write": "30/hour",
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

CORS_ALLOWED_ORIGINS = env_list(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:3001",
)
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = env_list(
    "CSRF_TRUSTED_ORIGINS",
    "http://localhost:3000,http://localhost:3001",
)

SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", not DEBUG)
SECURE_HSTS_SECONDS = int(os.getenv("DJANGO_SECURE_HSTS_SECONDS", "0" if DEBUG else "31536000"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

if env_bool("PIXELCORE_USE_S3", False):
    INSTALLED_APPS.append("storages")
    STORAGES = {
        "default": {"BACKEND": "storages.backends.s3.S3Storage"},
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }
    AWS_ACCESS_KEY_ID = os.environ["S3_ACCESS_KEY_ID"]
    AWS_SECRET_ACCESS_KEY = os.environ["S3_SECRET_ACCESS_KEY"]
    AWS_STORAGE_BUCKET_NAME = os.environ["S3_BUCKET_NAME"]
    AWS_S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL", "") or None
    AWS_S3_REGION_NAME = os.getenv("S3_REGION", "auto")
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = False

PIXELCORE_REFRESH_COOKIE = "pixelcore_refresh"
PIXELCORE_COOKIE_SECURE = not DEBUG
PIXELCORE_COOKIE_SAMESITE = os.getenv("PIXELCORE_COOKIE_SAMESITE", "Lax")
PIXELCORE_FRONTEND_URL = os.getenv("PIXELCORE_FRONTEND_URL", "http://localhost:3001")
PIXELCORE_PUBLIC_API_URL = os.getenv("PIXELCORE_PUBLIC_API_URL", "http://localhost:8000/api")
GOOGLE_CALENDAR_CLIENT_ID = os.getenv("GOOGLE_CALENDAR_CLIENT_ID", "")
GOOGLE_IDENTITY_CLIENT_ID = os.getenv("GOOGLE_IDENTITY_CLIENT_ID", GOOGLE_CALENDAR_CLIENT_ID)
GOOGLE_CALENDAR_CLIENT_SECRET = os.getenv("GOOGLE_CALENDAR_CLIENT_SECRET", "")
GOOGLE_CALENDAR_REDIRECT_URI = os.getenv(
    "GOOGLE_CALENDAR_REDIRECT_URI",
    "http://localhost:8000/api/google-calendar/callback/",
)

PIXELCORE_CADDY_AUTH_TOKEN = os.getenv("PIXELCORE_CADDY_AUTH_TOKEN", "")
PIXELCORE_PLATFORM_DOMAIN = os.getenv("PIXELCORE_PLATFORM_DOMAIN", "pixelcore.localhost")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1")
CELERY_TASK_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_TASK_ALWAYS_EAGER = env_bool("CELERY_TASK_ALWAYS_EAGER", False)
CELERY_TASK_EAGER_PROPAGATES = env_bool("CELERY_TASK_EAGER_PROPAGATES", False)
CELERY_BEAT_SCHEDULE = {
    "release-expired-stock-reservations": {
        "task": "operations.tasks.release_expired_stock_reservations",
        "schedule": 300.0,
    },
    "send-booking-reminders": {
        "task": "scheduling.tasks.send_booking_reminders",
        "schedule": 900.0,
    },
}

EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "PixelCore <noreply@pixelcore.local>")

# Optional installed shared builder; the sibling checkout is also a local development source.
WEBSITE_BUILDER_ROOT = Path(os.getenv("WEBSITE_BUILDER_ROOT", str(BASE_DIR.parent.parent / "website-builder")))
_builder_python = WEBSITE_BUILDER_ROOT / "python"
if (_builder_python / "website_builder").is_dir():
    sys.path.insert(0, str(_builder_python))
    INSTALLED_APPS.append("website_builder")
    WEBSITE_BUILDER_UPLOAD_MEDIA = "content.builder_bridge.upload_media"
    WEBSITE_BUILDER_AUTHORIZE = "content.builder_bridge.authorize"
    WEBSITE_BUILDER_RESOLVE_DATA = "content.builder_bridge.resolve_data"
    WEBSITE_BUILDER_REVIEW_DATA = "content.builder_bridge.review_data"
    WEBSITE_BUILDER_CAPABILITIES = "content.builder_bridge.capabilities"
    WEBSITE_BUILDER_AFTER_PUBLISH = "content.builder_bridge.after_publish"
    WEBSITE_BUILDER_VALIDATE_GLOBAL_PUBLISH = "content.builder_bridge.validate_global_publish"
    WEBSITE_BUILDER_FRONTEND_URL = PIXELCORE_FRONTEND_URL

STUDIO_FRONTEND_ORIGIN = os.getenv('STUDIO_FRONTEND_ORIGIN', 'http://localhost:4173')
_studio_client_file = BASE_DIR.parent.parent / 'website-builder' / '.data' / 'platform-client.key'
STUDIO_CLIENT_SECRET = os.getenv('STUDIO_CLIENT_SECRET', '') or (_studio_client_file.read_text().strip() if DEBUG and _studio_client_file.is_file() else '')

# Public builder pages expose an explicit per-business analytics choice.
WEBSITE_BUILDER_ANALYTICS_CONSENT_AVAILABLE = True
