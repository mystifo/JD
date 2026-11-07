"""Test settings: fast hashing, local memory cache, no transport redirects."""

import os

from .base import *  # noqa: F403

DEBUG = False
SECRET_KEY = "test-only-insecure-key-not-used-in-production"
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]

SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
TOKEN_HASH_SALT = os.environ.get("TOKEN_HASH_SALT", "test-only-salt")

# CI and local runs both point at the Compose PostgreSQL service unless overridden.
DATABASES["default"]["OPTIONS"]["sslmode"] = os.environ.get("DB_SSLMODE", "disable")  # noqa: F405

CONTENT_SECURITY_POLICY["DIRECTIVES"]["style-src"] = ["'self'", "'unsafe-inline'"]  # noqa: F405

# Throttling is exercised explicitly per test; the general limits stay enabled.
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["user"] = "10000/min"  # noqa: F405
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["anon"] = "10000/min"  # noqa: F405
