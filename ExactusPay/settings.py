# Services.py on Render
import os
import dj_database_url
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")

# DEBUG defaults to False on Render unless explicitly set to True
DEBUG = os.environ.get("DEBUG", "True") == "True"

# Security settings
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    USE_X_FORWARDED_HOST = True

# MUST be outside the DEBUG condition
ROOT_URLCONF = 'ExactusPay.urls'

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "exactuspay.onrender.com",
    "payroll.exactuspay.com",
    ".onrender.com",
]

CSRF_TRUSTED_ORIGINS = [
    "https://exactuspay.onrender.com",
    "https://payroll.exactuspay.com",
]

render_host = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if render_host:
    ALLOWED_HOSTS.append(render_host)
    CSRF_TRUSTED_ORIGINS.append(f"https://{render_host}")

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'crispy_forms',
    'crispy_bootstrap5',

    'accounts.apps.AccountsConfig',
    'country.apps.CountryConfig',
    'company',
    'regulations',
    'elements.apps.ElementsConfig',
    'calculationbase.apps.CalculationbaseConfig',
    'employee',
    'utils',  
    'pdcodes',  
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

WSGI_APPLICATION = 'ExactusPay.wsgi.application'

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / "templates",
            BASE_DIR / "Exactus" / "templates",
        ],
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

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Database configuration
if "DATABASE_URL" in os.environ:
    # Use Render's DATABASE_URL environment variable
    DATABASES = {
        "default": dj_database_url.config(
            default=os.environ["DATABASE_URL"],
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=True,
        )
    }
else:
    # Fallback for local development
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": "exactuspay_db",
            "USER": "exactuspay_db_user",
            "PASSWORD": "PhjN7vTmTch7tOLtvYtgqVUJO2xcbRly",
            "HOST": "dpg-d4fjqrumcj7s73apke3g-a.oregon-postgres.render.com",
            "PORT": "5432",
            "OPTIONS": {
                'sslmode': 'require',
            }
        }
    }

AUTH_USER_MODEL = 'accounts.User'

LANGUAGE_CODE = "en-gb"
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'