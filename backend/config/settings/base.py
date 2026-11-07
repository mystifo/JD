"""Base settings shared by every environment."""

from pathlib import Path

import environ

from config.logging import LOGGING  # noqa: F401

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    SESSION_COOKIE_SECURE=(bool, True),
    CSRF_COOKIE_SECURE=(bool, True),
    SECURE_SSL_REDIRECT=(bool, True),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")
APP_VERSION = env("APP_VERSION", default="1.0.0")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "rest_framework",
    "drf_spectacular",
    "django_filters",
    "csp",
    "apps.accounts",
    "apps.profiles",
    "apps.wellness",
    "apps.connections",
    "apps.journal",
    "apps.selfcare",
    "apps.calm_space",
    "apps.insights",
    "apps.notifications",
    "apps.privacy",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "csp.middleware.CSPMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.accounts.middleware.SessionVersionMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.privacy.middleware.RequestContextMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"
AUTH_USER_MODEL = "accounts.User"

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

DATABASES = {"default": env.db("DATABASE_URL")}
DATABASES["default"]["ATOMIC_REQUESTS"] = False
DATABASES["default"]["CONN_MAX_AGE"] = 60
DATABASES["default"].setdefault("OPTIONS", {})
DATABASES["default"]["OPTIONS"]["sslmode"] = env("DB_SSLMODE", default="prefer")

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_NAME = "sessionid"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = env("SESSION_COOKIE_SECURE")
SESSION_COOKIE_AGE = 12 * 60 * 60
SESSION_SAVE_EVERY_REQUEST = True
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = env("CSRF_COOKIE_SECURE")
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env("SECURE_SSL_REDIRECT")
SECURE_HSTS_SECONDS = 31_536_000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "herspace_cache",
        "TIMEOUT": 3600,
    }
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "common.pagination.StandardPagination",
    "PAGE_SIZE": 20,
    "EXCEPTION_HANDLER": "common.exceptions.api_exception_handler",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "common.throttling.GeneralUserThrottle",
        "common.throttling.GeneralAnonThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "60/min",
        "user": "300/min",
        "register": "5/hour",
        "login": "10/min",
        "login_email": "5/min",
        "password_reset": "10/hour",
        "password_reset_email": "3/hour",
        "password_reset_confirm": "10/hour",
        "verify_email": "10/hour",
        "verify_resend": "3/hour",
        "email_change": "3/day",
        "invite": "20/day",
        "invite_contact": "1/hour",
        "support_create": "10/hour",
        "public_invite": "30/hour",
        "public_invite_respond": "10/hour",
        "public_support": "60/hour",
        "public_support_respond": "10/hour",
        "export_request": "1/day",
        "export_download": "5/hour",
        "deletion": "3/day",
    },
}

SPECTACULAR_SETTINGS = {
    "TITLE": "HerSpace API",
    "DESCRIPTION": "Private wellness space API. Session cookie authentication.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
}

EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="HerSpace <hello@herspace.local>")
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_TIMEOUT = 10

TIME_ZONE = "UTC"
USE_TZ = True
LANGUAGE_CODE = "en"
USE_I18N = False

BASE_URL = env("BASE_URL", default="http://localhost:8000")
FRONTEND_BASE_URL = env("FRONTEND_BASE_URL", default="http://localhost:5173")
TOKEN_HASH_SALT = env("TOKEN_HASH_SALT", default="")
POLICY_TERMS_VERSION = env("POLICY_TERMS_VERSION", default="1.0")
POLICY_PRIVACY_VERSION = env("POLICY_PRIVACY_VERSION", default="1.0")
POLICY_WELLNESS_VERSION = env("POLICY_WELLNESS_VERSION", default="1.0")

STORAGE_ROOT = Path(env("PRIVATE_STORAGE_ROOT", default=str(BASE_DIR / "private_storage")))
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

DATA_UPLOAD_MAX_MEMORY_SIZE = 1_048_576

CONTENT_SECURITY_POLICY = {
    "DIRECTIVES": {
        "default-src": ["'self'"],
        "script-src": ["'self'"],
        "style-src": ["'self'"],
        "img-src": ["'self'", "data:"],
        "font-src": ["'self'"],
        "connect-src": ["'self'"],
        "frame-ancestors": ["'none'"],
        "base-uri": ["'none'"],
        "form-action": ["'self'"],
        "object-src": ["'none'"],
    }
}
