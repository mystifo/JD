"""Token issuance and validation helpers."""

from django.utils import timezone

from common.crypto import hash_ip, hash_token, new_token
from common.exceptions import TokenExpired, TokenInvalid, TokenUsed

from .models import EmailChangeRequest


def _request_ip_hash(request):
    if request is None:
        return None
    return hash_ip(request.META.get("REMOTE_ADDR"))


def issue_user_token(model, user, ttl, *, request=None):
    """Create a token row and return `(raw_token, row)`.

    The raw value exists only in this return value and the outgoing email.
    """
    raw = new_token()
    row = model.objects.create(
        user=user,
        token_hash=hash_token(raw),
        expires_at=timezone.now() + ttl,
        requested_ip_hash=_request_ip_hash(request),
    )
    return raw, row


def issue_email_change_request(user, new_email, ttl, *, request=None):
    raw = new_token()
    row = EmailChangeRequest.objects.create(
        user=user,
        new_email=new_email,
        token_hash=hash_token(raw),
        expires_at=timezone.now() + ttl,
    )
    return raw, row


def lookup_token(model, raw):
    """Resolve a raw token to an unused, unexpired row or raise."""
    if not raw:
        raise TokenInvalid("This link isn't valid. Request a new one.")
    row = model.objects.select_related("user").filter(token_hash=hash_token(raw)).first()
    if row is None:
        raise TokenInvalid("This link isn't valid. Request a new one.")
    if getattr(row, "used_at", None) is not None:
        raise TokenUsed("This link has already been used.")
    if row.expires_at <= timezone.now():
        raise TokenExpired("This link has expired. Request a new one.")
    return row


def lookup_email_change(raw):
    if not raw:
        raise TokenInvalid("This link isn't valid. Request a new one.")
    row = (
        EmailChangeRequest.objects.select_related("user").filter(token_hash=hash_token(raw)).first()
    )
    if row is None:
        raise TokenInvalid("This link isn't valid. Request a new one.")
    if row.confirmed_at is not None:
        raise TokenUsed("This link has already been used.")
    if row.expires_at <= timezone.now():
        raise TokenExpired("This link has expired. Request a new one.")
    return row
