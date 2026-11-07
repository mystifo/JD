"""Privacy and audit models.

`AuditEvent` is append-only by convention and by database grants in production
(security.md §9.4). No update or delete code paths exist.
"""

import uuid

from django.conf import settings
from django.db import models

from common.models import UUIDModel

AUDIT_EVENT_TYPES = (
    "auth.register",
    "auth.login",
    "auth.login_failed",
    "auth.lockout",
    "auth.logout",
    "auth.logout_all",
    "auth.email_verified",
    "auth.email_change_requested",
    "auth.email_changed",
    "auth.password_reset_requested",
    "auth.password_reset_completed",
    "auth.password_changed",
    "profile.updated",
    "preferences.updated",
    "onboarding.completed",
    "mood.saved",
    "mood.deleted",
    "journal.created",
    "journal.updated",
    "journal.deleted",
    "journal.searched",
    "contact.created",
    "contact.updated",
    "contact.deleted",
    "invitation.sent",
    "invitation.resent",
    "invitation.revoked",
    "invitation.responded",
    "support.requested",
    "support.responded",
    "support.cancelled",
    "support.expired",
    "support.share_revoked",
    "selfcare.routine_created",
    "selfcare.routine_updated",
    "selfcare.routine_deleted",
    "selfcare.completed",
    "selfcare.undone",
    "calm.session_recorded",
    "consent.granted",
    "consent.revoked",
    "export.requested",
    "export.ready",
    "export.downloaded",
    "export.expired",
    "export.failed",
    "deletion.scheduled",
    "deletion.cancelled",
    "deletion.completed",
    "notification.read",
    "notification.read_all",
    "security.rate_limited",
)

AUDIT_TARGET_TYPES = (
    "user",
    "mood_entry",
    "journal_entry",
    "contact",
    "invitation",
    "support_request",
    "export",
    "deletion",
)


class AuditEvent(UUIDModel):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_events",
    )
    actor_pseudonym = models.UUIDField(null=True, blank=True)
    event_type = models.CharField(max_length=48, choices=[(e, e) for e in AUDIT_EVENT_TYPES])
    target_type = models.CharField(  # noqa: DJ001 - nullable by schema; blank means "no target"
        max_length=32, null=True, blank=True, choices=[(t, t) for t in AUDIT_TARGET_TYPES]
    )
    target_id = models.UUIDField(null=True, blank=True)
    request_id = models.UUIDField(null=True, blank=True)
    ip_hash = models.CharField(max_length=64, null=True, blank=True)  # noqa: DJ001 - nullable
    user_agent_family = models.CharField(  # noqa: DJ001 - nullable
        max_length=40, null=True, blank=True
    )
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "privacy_auditevent"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(event_type__in=AUDIT_EVENT_TYPES),
                name="chk_auditevent_event_type",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(target_type__isnull=True, target_id__isnull=True)
                    | models.Q(target_type__isnull=False, target_id__isnull=False)
                ),
                name="chk_auditevent_target_pair",
            ),
        ]
        indexes = [
            models.Index(fields=["actor", "-created_at"], name="idx_auditevent_actor_created"),
            models.Index(fields=["event_type", "-created_at"], name="idx_auditevent_type_created"),
            models.Index(fields=["created_at"], name="idx_auditevent_created"),
        ]

    def __str__(self):
        return f"AuditEvent({self.event_type}, {self.pk})"

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValueError("AuditEvent rows are append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("AuditEvent rows cannot be deleted through the ORM.")


CONSENT_TYPES = (
    "terms_of_service",
    "privacy_policy",
    "wellness_disclaimer",
    "email_notifications",
    "support_request_sharing",
    "contact_invitation",
)

CONSENT_SCOPE_TYPES = (
    "support_request",
    "contact_invitation",
)


class ConsentRecord(UUIDModel):
    """Append-only proof of a consent decision.

    The latest row per `(user, consent_type, scope)` is the current state. A
    record is never edited except to stamp `revoked_at` when it is superseded
    or withdrawn (database-design.md §11.1).
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="consent_records",
    )
    consent_type = models.CharField(max_length=32, choices=[(c, c) for c in CONSENT_TYPES])
    policy_version = models.CharField(  # noqa: DJ001 - nullable by schema
        max_length=20, null=True, blank=True
    )
    scope_type = models.CharField(  # noqa: DJ001 - nullable by schema
        max_length=24, null=True, blank=True, choices=[(s, s) for s in CONSENT_SCOPE_TYPES]
    )
    scope_id = models.UUIDField(null=True, blank=True)
    granted = models.BooleanField()
    granted_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    ip_hash = models.CharField(max_length=64, null=True, blank=True)  # noqa: DJ001 - nullable
    user_agent_family = models.CharField(  # noqa: DJ001 - nullable
        max_length=40, null=True, blank=True
    )
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "privacy_consentrecord"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(consent_type__in=CONSENT_TYPES),
                name="chk_consentrecord_type",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(scope_type__isnull=True, scope_id__isnull=True)
                    | models.Q(scope_type__isnull=False, scope_id__isnull=False)
                ),
                name="chk_consentrecord_scope_pair",
            ),
            models.CheckConstraint(
                condition=models.Q(granted=True) | models.Q(revoked_at__isnull=False),
                name="chk_consentrecord_granted_state",
            ),
            models.CheckConstraint(
                condition=(
                    ~models.Q(consent_type__in=("terms_of_service", "privacy_policy"))
                    | models.Q(policy_version__isnull=False)
                ),
                name="chk_consentrecord_policy_version",
            ),
        ]
        indexes = [
            models.Index(
                fields=["user", "consent_type", "-created_at"],
                name="idx_consent_user_type_created",
            ),
            models.Index(fields=["scope_type", "scope_id"], name="idx_consent_scope"),
        ]

    def __str__(self):
        return f"ConsentRecord({self.consent_type}, {self.pk})"


def ensure_target_pair(target_type, target_id):
    """Normalise the pair so a mismatched half never reaches the DB."""
    if target_type is None or target_id is None:
        return None, None
    return target_type, uuid.UUID(str(target_id))
