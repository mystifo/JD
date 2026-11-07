"""Development settings: relaxed transport security, console email."""

import os

from .base import *  # noqa: F403

DEBUG = True

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-insecure-key-change-me")
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "backend", "testserver"]

DATABASES["default"]["OPTIONS"]["sslmode"] = os.environ.get("DB_SSLMODE", "disable")  # noqa: F405

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
TOKEN_HASH_SALT = os.environ.get("TOKEN_HASH_SALT", "dev-only-salt-change-me")

# Vite injects inline styles in dev only; never relax this in production.
CONTENT_SECURITY_POLICY["DIRECTIVES"]["style-src"] = ["'self'", "'unsafe-inline'"]  # noqa: F405

INTERNAL_IPS = ["127.0.0.1"]
