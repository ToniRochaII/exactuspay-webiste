import os
from pathlib import Path
import dj_database_url
from django.conf import settings

from django.test.utils import override_settings

ALLOWED = ["testserver", "localhost", "127.0.0.1"]

with override_settings(ALLOWED_HOSTS=ALLOWED):
    # everything that uses Client() / client.get() must be inside this block
    ...



# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ================================
# CORE SETTINGS
# ================================
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")

# In Render, ensure the environment variable DEBUG is set to "False".
DEBUG = os.environ.get("DEBUG", "True") == "True"

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "payroll.exactuspay.com",
    "testserver",
]

CSRF_TRUSTED_ORIGINS = [
    "https://payroll.exactuspay.com",
]

render_host = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if render_host:
    ALLOWED_HOSTS.append(render_host)
    CSRF_TRUSTED_ORIGINS.append(f"https://{render_host}")


# ================================
# INSTALLED APPS
# ================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'crispy_forms',
    'crispy_bootstrap5',
    'Exactus.accounts.apps.AccountsConfig',
    'Exactus.country.apps.CountryConfig',
    'Exactus.company',
    'Exactus.regulations',
    'Exactus.elements.apps.ElementsConfig',
    'Exactus.calculationbase.apps.CalculationbaseConfig',
    'Exactus.employee',
    'Exactus.utils',
    'Exactus.pdcodes',
    'Exactus.payroll',
    'Exactus.compensation',
    'Exactus.reports',
    'Exactus.ess.apps.EssConfig',
]

USE_I18N = True
USE_L10N = True  # optional (Django handles formatting well without it too)

LANGUAGE_CODE = "en"

LANGUAGES = [
    ("en", "English"),
    ("es", "Español"),
    ("pt", "Português"),
]


# Where your compiled translations will live (global)
LOCALE_PATHS = [BASE_DIR / "locale"]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "Exactus.accounts.middleware.UserPreferredLanguageMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = 'ExactusPay.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / "Exactus" / "templates",
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'Exactus.context_processors.sidebar_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'ExactusPay.wsgi.application'


# ================================
# DATABASE CONFIGURATION
# ================================
DATABASE_URL = os.environ.get("DATABASE_URL")

DATABASE_URL = (os.environ.get("DATABASE_URL") or "").strip()

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=60,   # 60 is a safer baseline than 600 on hosted DBs
        )
    }
    DATABASES["default"]["CONN_HEALTH_CHECKS"] = True

    # Only force SSL if you explicitly decide to via env var
    if os.environ.get("REQUIRE_DB_SSL", "0") == "1":
        DATABASES["default"].setdefault("OPTIONS", {})
        DATABASES["default"]["OPTIONS"]["sslmode"] = "require"
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# ================================
# CACHE CONFIGURATION
# ================================
if DEBUG:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'exactus-permissions',
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/1"),
        }
    }


# ================================
# PASSWORD VALIDATION
# ================================
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


# ================================
# INTERNATIONALIZATION
# ================================
LANGUAGE_CODE = "en-gb"
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# ================================
# STATIC & MEDIA FILES
# ================================
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'Exactus', 'static'),
]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# --- MEDIA FILES (UPLOADS) ---
MEDIA_URL = '/media/'

# FIX: Always save to project directory (works on Local & Render Standard)
MEDIA_ROOT = BASE_DIR / "media"


# ================================
# APP SETTINGS
# ================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"
AUTH_USER_MODEL = 'accounts.User'
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = 'role_based_redirect'
LOGOUT_REDIRECT_URL = "/login/"

FILE_UPLOAD_HANDLERS = [
    'django.core.files.uploadhandler.TemporaryFileUploadHandler',
]
PROGRESS_SESSION_KEY = 'upload_progress'


# ================================
# SECURITY SETTINGS
# ================================
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = 'Lax'

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    USE_X_FORWARDED_HOST = True
    SESSION_COOKIE_SECURE = True
else:
    SESSION_COOKIE_SECURE = False

SESSION_COOKIE_AGE = 2000
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_ENGINE = 'django.contrib.sessions.backends.db'


# ================================
# EMAIL CONFIGURATION (FORCE REAL SENDING)
# ================================

# Force SMTP backend to test real sending, even if DEBUG is True
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Hostinger Settings (Port 587 + TLS)
EMAIL_HOST = 'smtp.hostinger.com'
EMAIL_PORT = 465
EMAIL_USE_TLS = False   # StartTLS (Recommended for Cloud Hosting)
EMAIL_USE_SSL = True

EMAIL_HOST_USER = "no-reply@exactuspay.com"
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "").strip()

# Falha SEMPRE se faltar password quando usas SMTP real
if not EMAIL_HOST_PASSWORD:
    raise RuntimeError("EMAIL_HOST_PASSWORD is missing. Set it in Render env vars.")

DEFAULT_FROM_EMAIL = "no-reply@exactuspay.com"
DEMO_REQUEST_TO_EMAIL = os.environ.get("DEMO_REQUEST_TO_EMAIL", "antoniorocha@exactuspay.com").strip()

EMAIL_TIMEOUT = 20