"""Small validators shared by serializers."""

from urllib.parse import urlparse
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.core.exceptions import ValidationError


def validate_timezone(value: str) -> str:
    try:
        ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError, TypeError):
        raise ValidationError("Enter a valid time zone, for example Europe/Berlin.") from None
    return value


def safe_redirect_path(value: str, *, fallback: str = "/app") -> str:
    """Only allow same-origin, absolute-path redirects."""
    if not value:
        return fallback
    parsed = urlparse(value)
    if parsed.scheme or parsed.netloc or not value.startswith("/") or value.startswith("//"):
        return fallback
    return value


def is_safe_redirect(value: str) -> bool:
    return safe_redirect_path(value, fallback="") == value
