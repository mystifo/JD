"""Consent recording (database-design.md §11.1).

The latest row per `(user, consent_type, scope)` is current. Granting or
revoking supersedes prior active rows by stamping `revoked_at`; nothing else
about a row is ever changed.
"""

from django.db.models import Q
from django.utils import timezone

from common.audit import user_agent_family
from common.crypto import hash_ip

from ..models import CONSENT_SCOPE_TYPES, CONSENT_TYPES, ConsentRecord

POLICY_CONSENTS = frozenset({"terms_of_service", "privacy_policy"})
SCOPED_CONSENTS = {
    "support_request_sharing": "support_request",
    "contact_invitation": "contact_invitation",
}


def _evidence(request):
    if request is None:
        return None, None
    return (
        hash_ip(request.META.get("REMOTE_ADDR")),
        user_agent_family(request.headers.get("User-Agent")),
    )


def _validate(consent_type, scope_type, scope_id):
    if consent_type not in CONSENT_TYPES:
        raise ValueError(f"Unknown consent type: {consent_type}")
    if (scope_type is None) != (scope_id is None):
        raise ValueError("Consent scope_type and scope_id must be set together.")
    if scope_type is not None and scope_type not in CONSENT_SCOPE_TYPES:
        raise ValueError(f"Unknown consent scope type: {scope_type}")
    expected = SCOPED_CONSENTS.get(consent_type)
    if expected is not None and scope_type != expected:
        raise ValueError(f"Consent type {consent_type} requires scope {expected}.")


def _key_filter(user, consent_type, scope_type, scope_id):
    return Q(
        user=user,
        consent_type=consent_type,
        scope_type=scope_type,
        scope_id=scope_id,
    )


def _supersede(user, consent_type, scope_type, scope_id, now):
    ConsentRecord.objects.filter(
        _key_filter(user, consent_type, scope_type, scope_id),
        granted=True,
        revoked_at__isnull=True,
    ).update(revoked_at=now)


def grant(
    user,
    consent_type,
    *,
    policy_version=None,
    scope_type=None,
    scope_id=None,
    request=None,
    metadata=None,
):
    _validate(consent_type, scope_type, scope_id)
    if consent_type in POLICY_CONSENTS and not policy_version:
        raise ValueError("Policy consents require a policy_version.")
    now = timezone.now()
    ip_hash, ua_family = _evidence(request)
    _supersede(user, consent_type, scope_type, scope_id, now)
    return ConsentRecord.objects.create(
        user=user,
        consent_type=consent_type,
        policy_version=policy_version,
        scope_type=scope_type,
        scope_id=scope_id,
        granted=True,
        granted_at=now,
        ip_hash=ip_hash,
        user_agent_family=ua_family,
        metadata=metadata or {},
    )


def revoke(user, consent_type, *, scope_type=None, scope_id=None, request=None, metadata=None):
    _validate(consent_type, scope_type, scope_id)
    now = timezone.now()
    ip_hash, ua_family = _evidence(request)
    prior = ConsentRecord.objects.filter(
        _key_filter(user, consent_type, scope_type, scope_id),
        granted=True,
        revoked_at__isnull=True,
    )
    prior_info = {}
    latest = prior.order_by("-created_at").first()
    if latest is not None and latest.policy_version:
        prior_info["policy_version"] = latest.policy_version
    prior.update(revoked_at=now)
    return ConsentRecord.objects.create(
        user=user,
        consent_type=consent_type,
        policy_version=prior_info.get("policy_version"),
        scope_type=scope_type,
        scope_id=scope_id,
        granted=False,
        revoked_at=now,
        ip_hash=ip_hash,
        user_agent_family=ua_family,
        metadata=metadata or {},
    )


def is_granted(user, consent_type, *, scope_type=None, scope_id=None):
    row = (
        ConsentRecord.objects.filter(_key_filter(user, consent_type, scope_type, scope_id))
        .order_by("-created_at")
        .first()
    )
    return bool(row and row.granted)


def set_email_notifications(user, enabled, *, request=None):
    """Mirror the preference into consent proof (api-documentation.md §5.4)."""
    if enabled:
        return grant(user, "email_notifications", request=request)
    return revoke(user, "email_notifications", request=request)
