import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR.parent / ".env")
load_dotenv(BASE_DIR / ".env")


REQUIRED_ENV_VARS = (
    "DJANGO_SECRET_KEY",
    "DJANGO_ALLOWED_HOSTS",
    "DB_NAME",
    "DB_USER",
    "DB_PASSWORD",
    "DB_HOST",
    "CORS_ALLOWED_ORIGINS",
)

_missing = [name for name in REQUIRED_ENV_VARS if os.getenv(name) is None]
if _missing:
    raise ImproperlyConfigured(
        "Missing required environment variable(s): "
        + ", ".join(_missing)
        + ". See .env.example for the full list."
    )


def _env_required(name: str) -> str:
    value = os.environ[name].strip()
    if not value:
        raise ImproperlyConfigured(f"Environment variable {name} must not be empty.")
    return value


def _env_list(name: str) -> list[str]:
    return [item.strip() for item in _env_required(name).split(",") if item.strip()]


SECRET_KEY = _env_required("DJANGO_SECRET_KEY")
DEBUG = os.getenv("DJANGO_DEBUG", "0") == "1"
ALLOWED_HOSTS = _env_list("DJANGO_ALLOWED_HOSTS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "meetings",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
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
    },
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": _env_required("DB_NAME"),
        "USER": _env_required("DB_USER"),
        # May be empty when the database uses trust/peer authentication.
        "PASSWORD": os.environ["DB_PASSWORD"],
        "HOST": _env_required("DB_HOST"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}

AUTH_PASSWORD_VALIDATORS = []
LANGUAGE_CODE = "en-gb"
TIME_ZONE = os.getenv("APP_TIME_ZONE", "Asia/Kolkata")
USE_I18N = True
USE_TZ = False  # Rooms and bookings use the office's local wall-clock time.

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "EXCEPTION_HANDLER": "meetings.exceptions.exception_handler",
}

CORS_ALLOWED_ORIGINS = _env_list("CORS_ALLOWED_ORIGINS")
