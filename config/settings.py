import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    from django.core.management.utils import get_random_secret_key
    if os.getenv("DEBUG", "False").lower() == "true":
        SECRET_KEY = get_random_secret_key()
    else:
        raise ValueError("SECRET_KEY environment variable is required in production")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# Development settings for better error handling
if DEBUG:
    INTERNAL_IPS = ["127.0.0.1", "localhost"]

# Production ALLOWED_HOSTS for cPanel
ALLOWED_HOSTS = [
    "roshandamor.me",
    "www.roshandamor.me",
    "127.0.0.1",
    "localhost",
]

# Add environment variable support for dynamic hosts
env_hosts = os.getenv("ALLOWED_HOSTS", "")
if env_hosts:
    ALLOWED_HOSTS.extend(
        [host.strip() for host in env_hosts.split(",") if host.strip()]
    )

# API Keys and External Services
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TINYMCE_API_KEY = os.getenv("TINYMCE_API_KEY", "")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "corsheaders",
    "tinymce",
    "portfolio",
    "blog",
    "ai",
    "authentication",
    "roshan",
    "notifications",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

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
                "portfolio.context_processors.site_context",
                "config.admin_context.admin_dashboard_context",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Database Configuration for cPanel MySQL
if DEBUG:
    # Local development with SQLite
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    # Production cPanel MySQL
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.getenv("MYSQL_DB", "portfolio_db"),
            "USER": os.getenv("MYSQL_USER", "portfolio_user"),
            "PASSWORD": os.getenv("MYSQL_PASSWORD", ""),
            "HOST": os.getenv("MYSQL_HOST", "localhost"),
            "PORT": os.getenv("MYSQL_PORT", "3306"),
            "OPTIONS": {
                "charset": "utf8mb4",
                "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
            },
        }
    }


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "en-in"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True


# Static files configuration for cPanel
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# WhiteNoise configuration for serving static files
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Media files configuration
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# TinyMCE Configuration
TINYMCE_DEFAULT_CONFIG = {
    "height": 500,
    "width": "100%",
    "cleanup_on_startup": True,
    "custom_undo_redo_levels": 20,
    "plugins": """
        advlist autolink lists link image charmap preview anchor
        searchreplace wordcount visualblocks code fullscreen
        insertdatetime media table emoticons
    """,
    "toolbar": """
        undo redo | bold italic underline | alignleft aligncenter alignright |
        bullist numlist | link image media | code preview fullscreen |
        emoticons charmap
    """,
    "menubar": True,
    "statusbar": True,
}


# Email Configuration
if DEBUG:
    # Development: Console backend
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
else:
    # Production: SMTP backend for cPanel
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = os.getenv("EMAIL_HOST", "mail.roshandamor.me")
    EMAIL_PORT = int(os.getenv("EMAIL_PORT", "465"))
    EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "False").lower() == "true"
    EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "True").lower() == "true"
    EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "noreply@roshandamor.me")
    EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
    DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@roshandamor.me")
    SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Site Configuration
SITE_NAME = os.getenv("SITE_NAME", "Roshan Damor Portfolio")
SITE_URL = os.getenv(
    "SITE_URL", "https://roshandamor.me" if not DEBUG else "http://localhost:8000"
)

# Message tags for Bootstrap
from django.contrib.messages import constants as messages

MESSAGE_TAGS = {
    messages.DEBUG: "debug",
    messages.INFO: "info",
    messages.SUCCESS: "success",
    messages.WARNING: "warning",
    messages.ERROR: "danger",
}

# Security Settings for Production
if not DEBUG:
    # HTTPS and Security
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = True

    # Session Security
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = True

# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    "https://roshandamor.me",
    "https://www.roshandamor.me",
]

if DEBUG:
    CORS_ALLOWED_ORIGINS.extend(
        [
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ]
    )

# Logging Configuration
# Ensure logs directory exists
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": LOGS_DIR / "notifications.log",
            "formatter": "verbose",
        },
        "console": {
            "level": "DEBUG" if DEBUG else "INFO",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "loggers": {
        "notifications": {
            "handlers": ["file", "console"] if not os.getenv('CI') else ["console"],
            "level": "INFO",
            "propagate": True,
        },
        "django": {
            "handlers": ["console"],
            "level": "INFO" if DEBUG else "WARNING",
            "propagate": False,
        },
        "django.contrib.admin": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": True,
        },
    },
}
