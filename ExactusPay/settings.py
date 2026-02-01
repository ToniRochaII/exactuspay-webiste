import os
from pathlib import Path
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ================================
# CORE SETTINGS
# ================================
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")

# SECURITY WARNING: don't run with debug turned on in production!
# In Render, ensure the environment variable DEBUG is set to "False".
DEBUG = os.environ.get("DEBUG", "True") == "True"

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "payroll.exactuspay.com",
]

CSRF_TRUSTED_ORIGINS = [
    "https://payroll.exactuspay.com",
]

# Add Render external hostname automatically if available
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
    'Exactus.reports',
    'Exactus.ess.apps.EssConfig',
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    
    # Custom Session Middleware (Uncomment if needed)
    # "Exactus.middleware.session_timeout.SessionTimeoutMiddleware",
    # "Exactus.middleware.tab_close_detection.TabCloseMiddleware",
    
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
# If DATABASE_URL is set (Production), we use it.
# If not (Local), we use db.sqlite3.
DATABASE_URL = os.environ.get("DATABASE_URL")

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


# ================================
# CACHE CONFIGURATION (UPDATED)
# ================================
if DEBUG:
    # Local memory cache for development
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'exactus-permissions',
        }
    }
else:
    # Production Redis Cache (Updated to support Render's REDIS_URL)
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            # Use Render's REDIS_URL if available, fallback to localhost
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

# WhiteNoise: Optimization for serving static files in production
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# ================================
# APP SETTINGS
# ================================
# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Authentication URLs
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = 'role_based_redirect'
LOGOUT_REDIRECT_URL = "/login/"

# File Upload Settings
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

# Session Configuration
SESSION_COOKIE_AGE = 2000
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_ENGINE = 'django.contrib.sessions.backends.db'


# ================================
# EMAIL CONFIGURATION (FIXED)
# ================================
# 1. Determine Backend:
# If DEBUG is True, use Console (prints to terminal) to prevent browser hanging during local dev.
# If DEBUG is False (Production), use SMTP.


    
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Hostinger SMTP Settings
EMAIL_HOST = 'smtp.hostinger.com'
EMAIL_PORT = 465

# --- CRITICAL FIX START ---
# Port 465 requires Implicit SSL. 
# We MUST set USE_SSL=True and USE_TLS=False to avoid hanging connections.
EMAIL_USE_SSL = True   
EMAIL_USE_TLS = False  
# --- CRITICAL FIX END ---

EMAIL_HOST_USER = 'no-reply@exactuspay.com'

# SECURITY: Try to get password from Environment Variable first.
# If you haven't set the Env Var yet, replace "PASSWORD_HERE" with the real password.
EMAIL_HOST_PASSWORD = os.environ.get("TlBFI=[b2L") 

DEFAULT_FROM_EMAIL = 'Exactus Support <no-reply@exactuspay.com>'