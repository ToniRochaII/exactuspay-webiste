from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
DEBUG = os.environ.get("DEBUG", "0") == "1"


ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "exactuspay.com",
    "www.exactuspay.com",
    ".onrender.com",
]

CSRF_TRUSTED_ORIGINS = [
    "https://exactuspay.com",
    "https://www.exactuspay.com",
    "http://127.0.0.1",
    "http://localhost",
]

# Render / proxy headers (safe to keep)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts.apps.AccountsConfig",
    "home",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",  # must be after sessions
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
                "home.context_processors.site_context",
            ],
        },
    }
]

WSGI_APPLICATION = "ExactusPay.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# i18n
LANGUAGE_CODE = "en"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ("en", "English"),
    ("ar", "Arabic"),
    ("de", "German"),
    ("es", "Español"),
    ("fr", "French"),
    ("id", "Indonesian"),
    ("it", "Italian"),
    ("pl", "Polish"),
    ("pt", "Português"),
    ("ru", "Russian"),
    ("sw", "Swahili"),
    ("th", "Thai"),
]

LOCALE_PATHS = [BASE_DIR / "locale"]

# static
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "accounts:profile"
LOGOUT_REDIRECT_URL = "home:home"

EXTERNAL_PAYROLL_LOGIN_URL = os.environ.get(
    "EXTERNAL_PAYROLL_LOGIN_URL",
    "https://payroll.exactuspay.com/login",
)
BOOK_DEMO_EXTERNAL_URL = os.environ.get(
    "BOOK_DEMO_EXTERNAL_URL",
    "https://outlook.office.com/bookwithme/user/42af7574f874421f894f9f248bece5ed@exactuspay.com?anonymous&ismsaljsauthenabled&ep=plink",
)


# -----------------------------------------------------------------------------
# Email (Hostinger / ExtendCP SMTP)
# -----------------------------------------------------------------------------

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.office365.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False

EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "Antonio.Rocha@exactuspay.com")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
NO_REPLY_EMAIL = os.environ.get("NO_REPLY_EMAIL", "no-reply@exactuspay.com")

DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL",
    NO_REPLY_EMAIL,
)

# Where demo requests should be delivered
DEMO_REQUEST_TO_EMAIL = os.environ.get(
    "DEMO_REQUEST_TO_EMAIL",
    "Antonio.Rocha@exactuspay.com",
)

SERVER_EMAIL = DEFAULT_FROM_EMAIL
EMAIL_TIMEOUT = 20
