from __future__ import annotations

import os
import os
print("DEBUG=", os.getenv("DEBUG"))
print("SECRET_KEY exists? ", bool(os.getenv("SECRET_KEY")))

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# -----------------------------------------------------------------------------
# Core
# -----------------------------------------------------------------------------
DEBUG = os.environ.get("DEBUG", "").lower() in ("1", "true", "yes", "on")

SECRET_KEY = os.environ.get("SECRET_KEY") or ("dev-secret-key" if DEBUG else None)
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY missing in production (DEBUG=False). Set it in Render env vars.")

SECRET_KEY = SECRET_KEY or "dev-secret-key"

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "exactuspay.com",
    "www.exactuspay.com",
    ".onrender.com",
]

# If Render provides an external URL, trust it for CSRF too
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL", "").strip()

CSRF_TRUSTED_ORIGINS = [
    "https://exactuspay.com",
    "https://www.exactuspay.com",
]
if RENDER_EXTERNAL_URL.startswith("https://"):
    CSRF_TRUSTED_ORIGINS.append(RENDER_EXTERNAL_URL)

if DEBUG:
    CSRF_TRUSTED_ORIGINS += [
        "http://127.0.0.1",
        "http://localhost",
        "https://127.0.0.1",
        "https://localhost",
    ]

# Render / proxy headers (safe to keep)
# Render commonly sets one of these vars; using either is more robust than RENDER=="true"
if os.environ.get("RENDER") or RENDER_EXTERNAL_URL:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    USE_X_FORWARDED_HOST = True

# -----------------------------------------------------------------------------
# Apps / Middleware
# -----------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "home",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "ExactusPay.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
            ],
        },
    }
]

WSGI_APPLICATION = "ExactusPay.wsgi.application"

# -----------------------------------------------------------------------------
# Database
# -----------------------------------------------------------------------------
# Marketing website can be SQLite; Render filesystem may be ephemeral.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# -----------------------------------------------------------------------------
# Password validation
# -----------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# -----------------------------------------------------------------------------
# i18n / l10n
# -----------------------------------------------------------------------------
LANGUAGE_CODE = "en"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Per your preference: Portuguese translations (no Spanish)
LANGUAGES = [
    ("en", "English"),
    ("pt", "Português"),
    ("es", "Español"),
    ("ru", "Русский"),
    ("sa", "Saudí"),
]

LOCALE_PATHS = [BASE_DIR / "locale"]

# -----------------------------------------------------------------------------
# Static files (WhiteNoise)
# -----------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Only include STATICFILES_DIRS if the folder exists (avoids warnings)
_static_dir = BASE_DIR / "static"
STATICFILES_DIRS = [_static_dir] if _static_dir.exists() else []

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# -----------------------------------------------------------------------------
# Email (Hostinger SMTP over SSL 465)
# -----------------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.hostinger.com"
EMAIL_PORT = 465
EMAIL_USE_TLS = False
EMAIL_USE_SSL = True

EMAIL_HOST_USER = "no-reply@exactuspay.com"
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")

DEFAULT_FROM_EMAIL = "Exactus Support <no-reply@exactuspay.com>"
DEMO_REQUEST_TO_EMAIL = os.environ.get("DEMO_REQUEST_TO_EMAIL", "antoniorocha@exactuspay.com")

# -----------------------------------------------------------------------------
# Security (production)
# -----------------------------------------------------------------------------
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True

    # Recommended security headers
    SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "3600"))  # start small; raise to 31536000 later
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
    X_FRAME_OPTIONS = "DENY"
