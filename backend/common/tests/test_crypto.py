from common.crypto import (
    email_fingerprint,
    hash_ip,
    hash_token,
    mask_email,
    new_token,
    pseudonym_for,
    verify_token,
)


def test_tokens_are_url_safe_and_unique():
    tokens = {new_token() for _ in range(50)}
    assert len(tokens) == 50
    assert all(len(token) >= 40 for token in tokens)
    assert all(all(c.isalnum() or c in "-_" for c in token) for token in tokens)


def test_hash_is_stable_and_verify_uses_constant_time_compare():
    raw = new_token()
    digest = hash_token(raw)
    assert digest == hash_token(raw)
    assert len(digest) == 64
    assert verify_token(raw, digest)
    assert not verify_token(raw + "x", digest)
    assert not verify_token("", digest)
    assert not verify_token(raw, "")


def test_ip_hash_is_salted(settings):
    settings.TOKEN_HASH_SALT = "salt-a"
    first = hash_ip("203.0.113.5")
    settings.TOKEN_HASH_SALT = "salt-b"
    second = hash_ip("203.0.113.5")

    assert first != second
    assert len(first) == 64
    assert hash_ip(None) is None


def test_pseudonym_is_stable_and_distinct():
    import uuid

    user_id = uuid.uuid4()
    assert pseudonym_for(user_id) == pseudonym_for(user_id)
    assert pseudonym_for(user_id) != pseudonym_for(uuid.uuid4())


def test_mask_email_keeps_only_the_domain():
    assert mask_email("mira@example.com") == "m***@example.com"
    assert mask_email("not-an-email") == "***"
    assert mask_email(None) == "***"


def test_email_fingerprint_is_not_reversible(settings):
    settings.TOKEN_HASH_SALT = "salt"
    digest = email_fingerprint("Owner@Example.com")
    assert len(digest) == 12
    assert "owner" not in digest.lower()
    assert digest == email_fingerprint("owner@example.com")
