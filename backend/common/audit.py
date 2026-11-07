"""Append-only audit trail helper.

Every security-relevant action calls `record()` from inside the same database
transaction as the action it describes. Metadata is restricted to counts and
enums — never free text, never user content (BR-10).
"""

import re

from common.crypto import hash_ip, pseudonym_for

FORBIDDEN_METADATA_KEYS = frozenset(
    {
        "content",
        "note",
        "message",
        "response_note",
        "snapshot",
        "email",
        "phone",
        "title",
        "body",
        "q",
        "search",
        "password",
        "token",
    }
)

TARGET_TYPES = {
    "user": "user",
    "moodentry": "mood_entry",
    "journalentry": "journal_entry",
    "trustedcontact": "contact",
    "contactinvitation": "invitation",
    "supportrequest": "support_request",
    "dataexportrequest": "export",
    "accountdeletionrequest": "deletion",
}

_UA_RE = re.compile(r"(Chrome|Firefox|Safari|Edg|Opera|OPR)/[\d.]+")


def user_agent_family(value: str | None) -> str | None:
    if not value:
        return None
    match = _UA_RE.search(value)
    if match:
        family = "Edge" if match.group(1) in {"Edg", "Edge"} else match.group(1)
        return f"{family}/{match.group(0).split('/')[-1]}"
    return value[:40]


def _validate_metadata(metadata):
    if not isinstance(metadata, dict):
        raise ValueError("Audit metadata must be a dict.")
    for key, value in metadata.items():
        if str(key).lower() in FORBIDDEN_METADATA_KEYS:
            raise ValueError(f"Audit metadata key '{key}' may contain user content.")
        if isinstance(value, (dict, tuple)):
            raise ValueError("Audit metadata values must be scalars or lists.")
        if isinstance(value, list) and any(isinstance(item, (dict, list)) for item in value):
            raise ValueError("Audit metadata lists must contain scalars only.")


def record(
    actor,
    event_type,
    *,
    target=None,
    target_type=None,
    target_id=None,
    request=None,
    metadata=None,
):
    """Write one AuditEvent and return it."""
    from apps.privacy.models import AUDIT_EVENT_TYPES, AuditEvent, ensure_target_pair

    if event_type not in AUDIT_EVENT_TYPES:
        raise ValueError(f"Unknown audit event type: {event_type}")

    metadata = metadata or {}
    _validate_metadata(metadata)

    if target is not None and target_type is None:
        target_type = TARGET_TYPES.get(target.__class__.__name__.lower())
        target_id = target.pk
    target_type, target_id = ensure_target_pair(target_type, target_id)

    request_id = getattr(request, "request_id", None) if request is not None else None
    ip = None
    ua = None
    if request is not None:
        ip = hash_ip(request.META.get("REMOTE_ADDR"))
        ua = user_agent_family(request.headers.get("User-Agent"))

    return AuditEvent.objects.create(
        actor=actor if getattr(actor, "pk", None) else None,
        actor_pseudonym=pseudonym_for(actor.pk) if getattr(actor, "pk", None) else None,
        event_type=event_type,
        target_type=target_type,
        target_id=target_id,
        request_id=request_id,
        ip_hash=ip,
        user_agent_family=ua,
        metadata=metadata,
    )
