"""Production settings: fail closed on missing secrets."""

from .base import *  # noqa: F403

DEBUG = False
ALLOWED_HOSTS = env("ALLOWED_HOSTS")  # noqa: F405

if len(SECRET_KEY) < 32:  # noqa: F405
    raise RuntimeError("DJANGO_SECRET_KEY must be at least 32 characters in production.")
if not TOKEN_HASH_SALT:  # noqa: F405
    raise RuntimeError("TOKEN_HASH_SALT is required in production.")

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31_536_000

EMAIL_BACKEND = env(
    "EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend"
)  # noqa: F405

LOGGING["handlers"]["console"]["level"] = "INFO"  # noqa: F405
