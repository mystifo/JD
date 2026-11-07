"""Token generation, hashing, and pseudonymisation helpers.

Tokens are 256-bit URL-safe secrets stored only as SHA-256 digests. They are
never logged and never placed in URLs that appear in access logs without
redaction (see `common.logging_filters`).
"""

import hashlib
import hmac
import re
import secrets
import uuid

from django.conf import settings

PSEUDONYM_NAMESPACE = uuid.UUID("6f9619ff-8b86-d011-b42d-00c04fc964ff")

_EMAIL_RE = re.compile(r"^[^@]+@[^@]+\.[^@]+$")


def new_token() -> str:
    """Return a 256-bit URL-safe token (43 characters)."""
    return secrets.token_urlsafe(32)


def hash_token(raw: str) -> str:
    """SHA-256 hex digest. Unsalted by design: the input is high entropy."""
    return hashlib.sha256(raw.encode()).hexdigest()


def verify_token(raw: str, stored_hash: str) -> bool:
    if not raw or not stored_hash:
        return False
    return hmac.compare_digest(hash_token(raw), stored_hash)


def hash_ip(ip: str | None) -> str | None:
    """Salted SHA-256 of an IP address, or None when unknown."""
    if not ip:
        return None
    salt = settings.TOKEN_HASH_SALT or ""
    return hashlib.sha256(f"{salt}:{ip}".encode()).hexdigest()


def pseudonym_for(user_id) -> uuid.UUID:
    """Stable UUID pseudonym that survives account deletion."""
    return uuid.uuid5(PSEUDONYM_NAMESPACE, str(user_id))


def email_fingerprint(email: str) -> str:
    """First 12 hex characters of a salted email hash, for log correlation."""
    salt = settings.TOKEN_HASH_SALT or ""
    digest = hashlib.sha256(f"{salt}:{email.strip().lower()}".encode()).hexdigest()
    return digest[:12]


def mask_email(email: str | None) -> str:
    """`mira@example.com` -> `m***@example.com`. Safe for UI display."""
    if not email or not _EMAIL_RE.match(email):
        return "***"
    local, domain = email.split("@", 1)
    head = local[:1] if local else ""
    return f"{head}***@{domain}"
