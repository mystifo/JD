"""In-app notifications. Bodies are template-generated and never contain user content."""

from django.conf import settings
from django.db import models

from common.models import UUIDModel

NOTIFICATION_CATEGORIES = (
    "mood_reminder",
    "routine_reminder",
    "support_request_sent",
    "support_request_response",
    "support_request_expired",
    "invitation_accepted",
    "invitation_declined",
    "data_export_ready",
    "account_deletion_scheduled",
    "security_alert",
    "system",
)


class Notification(UUIDModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    category = models.CharField(max_length=32, choices=[(c, c) for c in NOTIFICATION_CATEGORIES])
    title = models.CharField(max_length=120)
    body = models.CharField(max_length=300)
    link_path = models.CharField(  # noqa: DJ001 - nullable by schema
        max_length=200, null=True, blank=True
    )
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "notifications_notification"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(category__in=NOTIFICATION_CATEGORIES),
                name="chk_notification_category",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(is_read=False, read_at__isnull=True)
                    | models.Q(is_read=True, read_at__isnull=False)
                ),
                name="chk_notification_read_consistency",
            ),
            models.CheckConstraint(
                condition=models.Q(link_path__isnull=True) | models.Q(link_path__startswith="/"),
                name="chk_notification_link_path",
            ),
        ]
        indexes = [
            models.Index(
                fields=["user", "is_read", "-created_at"],
                name="idx_notification_user_unread",
            ),
            models.Index(fields=["expires_at"], name="idx_notification_expiry"),
        ]

    def __str__(self):
        # No title/body in log output.
        return f"Notification({self.category}, {self.pk})"
