"""
Django settings for swipepoint project.
"""

import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-change-me-in-production")
DEBUG = os.environ.get("DEBUG", "False").lower() in ("1", "true", "yes")

# Comma-separated hostnames, or "*" to allow any (typical on PaaS when paired with a reverse proxy).
_allowed = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").strip()
if not _allowed:
    _allowed = "localhost,127.0.0.1"
ALLOWED_HOSTS = ["*"] if _allowed == "*" else [h.strip() for h in _allowed.split(",") if h.strip()]
if not ALLOWED_HOSTS:
    ALLOWED_HOSTS = ["*"]

# Railway: without ALLOWED_HOSTS in the dashboard, the public *.up.railway.app Host header
# triggers DisallowedHost → HTTP 400. Wildcard subdomain + optional RAILWAY_PUBLIC_DOMAIN.
_on_railway = bool(
    os.environ.get("RAILWAY_ENVIRONMENT")
    or os.environ.get("RAILWAY_PUBLIC_DOMAIN")
    or os.environ.get("RAILWAY_PROJECT_ID")
)
if _on_railway and ALLOWED_HOSTS != ["*"]:
    _railway_public = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "").strip()
    if _railway_public and _railway_public not in ALLOWED_HOSTS:
        ALLOWED_HOSTS = [*ALLOWED_HOSTS, _railway_public]
    if ".up.railway.app" not in ALLOWED_HOSTS:
        ALLOWED_HOSTS = [*ALLOWED_HOSTS, ".up.railway.app"]

# If your app is behind a proxy/load balancer, let Django detect HTTPS correctly.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# Prefer the public Host from the edge proxy (Railway, etc.).
USE_X_FORWARDED_HOST = _on_railway

# HTTPS origins for CSRF (e.g. https://your-app.up.railway.app). Comma-separated.
CSRF_TRUSTED_ORIGINS = [
    x.strip()
    for x in os.environ.get("CSRF_TRUSTED_ORIGINS", "").split(",")
    if x.strip()
]
_railway_public_domain = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "").strip()
if _railway_public_domain:
    _railway_csrf = f"https://{_railway_public_domain}"
    if _railway_csrf not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS = [*CSRF_TRUSTED_ORIGINS, _railway_csrf]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "payments",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "swipepoint.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "swipepoint.wsgi.application"

_database_url = os.environ.get("DATABASE_URL")
if _database_url:
    DATABASES = {
        "default": dj_database_url.config(
            default=_database_url,
            conn_max_age=600,
            ssl_require=True,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
        ),
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
}

CORS_ALLOW_ALL_ORIGINS = DEBUG

if not DEBUG:
    CORS_ALLOWED_ORIGINS = [
        o.strip()
        for o in os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",")
        if o.strip()
    ]

SWIPEPOINT_API_SECRET = os.environ.get("SWIPEPOINT_API_SECRET", "")
SWIPEPOINT_CHARGE_URL = os.environ.get(
    "SWIPEPOINT_CHARGE_URL",
    "https://swipepointe.com/api/charge",
)

PAYMENT_PROVIDER_MODE = os.environ.get("PAYMENT_PROVIDER_MODE", "internal")
