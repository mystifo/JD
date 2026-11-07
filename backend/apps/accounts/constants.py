"""Authentication constants from security.md and api-documentation.md."""

from datetime import timedelta

EMAIL_VERIFICATION_TTL = timedelta(hours=24)
PASSWORD_RESET_TTL = timedelta(minutes=60)
EMAIL_CHANGE_TTL = timedelta(hours=2)

LOCKOUT_THRESHOLD = 10
LOCKOUT_DURATION = timedelta(minutes=15)

DEFAULT_TIMEZONE = "UTC"
