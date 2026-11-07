"""Notification producers shared by other apps.

M2 only needs the security-notice producer; the feed and reminder jobs belong
to M8. Message text is fixed and never interpolates private content (BR-10).
"""

from datetime import timedelta

from django.utils import timezone

from .models import Notification

SECURITY_LINK = "/app/settings/security"

SECURITY_MESSAGES = {
    "logout_all": (
        "You were signed out on other devices",
        "All other sessions were ended. If this wasn't you, reset your password.",
    ),
    "password_changed": (
        "Your password was changed",
        "All other sessions were ended. If this wasn't you, reset your password.",
    ),
    "password_reset": (
        "Your password was reset",
        "All sessions were signed out. If this wasn't you, reset your password again.",
    ),
}


def notify_security(user, reason):
    """Create a `security_alert` notification with fixed, content-free copy."""
    try:
        title, body = SECURITY_MESSAGES[reason]
    except KeyError as exc:
        raise ValueError(f"Unknown security notification reason: {reason}") from exc
    return Notification.objects.create(
        user=user,
        category="security_alert",
        title=title,
        body=body,
        link_path=SECURITY_LINK,
        expires_at=timezone.now() + timedelta(days=90),
    )
