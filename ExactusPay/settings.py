# settings.py
import os
from pathlib import Path
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")

# SECURITY WARNING: don't run with debug turned on in production!
# Defaults to True only if the variable is not set. In Render, set this to "False".
DEBUG = os.environ.get("DEBUG", "True") == "True"

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    
    # Third-party apps
    'crispy_forms',
    'crispy_bootstrap5',
    
    # Local apps
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
                # Duplicate removed here
                'Exactus.context_processors.sidebar_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'ExactusPay.wsgi.application'

# ================================
# DATABASE CONFIGURATION
# ================================
# If DATABASE_URL is set (Production), we use it.
# If not (Local), we use db.sqlite3.
DATABASE_URL = os.environ.get("DATABASE_URL")

# Check if DATABASE_URL exists AND is not just whitespace
if DATABASE_URL and DATABASE_URL.strip():
    DATABASES = {
        "default": dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=True,
        )
    }
else:
    # Local development uses SQLite
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Password validation
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

# Internationalization
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

# WhiteNoise: Optimization for serving static files in production
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Authentication URLs
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/login/"

# ================================
# HOSTS & SECURITY
# ================================
ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "payroll.exactuspay.com",
]

CSRF_TRUSTED_ORIGINS = [
    "https://payroll.exactuspay.com",
]

# Add Render external hostname if available
render_host = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if render_host:
    ALLOWED_HOSTS.append(render_host)
    CSRF_TRUSTED_ORIGINS.append(f"https://{render_host}")

# Security Settings
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = 'Lax'

if not DEBUG:
    # Production settings
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    USE_X_FORWARDED_HOST = True
    SESSION_COOKIE_SECURE = True
else:
    # Development settings
    SESSION_COOKIE_SECURE = False

# Cache Configuration
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
            'LOCATION': 'redis://127.0.0.1:6379/1',
        }
    }


# ================================
# SESSION CONFIGURATION
# ================================
SESSION_COOKIE_AGE = 2000
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_ENGINE = 'django.contrib.sessions.backends.db'


# ================================
# MIDDLEWARE
# ================================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    
    # Custom Session Middleware (MUST come after AuthenticationMiddleware)
    # "Exactus.middleware.session_timeout.SessionTimeoutMiddleware",
    # "Exactus.middleware.tab_close_detection.TabCloseMiddleware",
    
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# File Upload Settings
FILE_UPLOAD_HANDLERS = [
    'django.core.files.uploadhandler.TemporaryFileUploadHandler',
]

PROGRESS_SESSION_KEY = 'upload_progress'