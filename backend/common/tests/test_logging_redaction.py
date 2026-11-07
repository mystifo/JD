import io
import json
import logging

from common.logging_filters import JsonFormatter, RedactSensitiveFilter, mask_path

SENTINEL = "HS_SENTINEL_9f3a7c"


def _capture():
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    handler.addFilter(RedactSensitiveFilter())
    logger = logging.getLogger(f"test.redaction.{id(stream)}")
    logger.handlers = [handler]
    logger.propagate = False
    logger.setLevel(logging.INFO)
    return logger, stream


def test_sentinel_in_message_is_redacted():
    logger, stream = _capture()
    logger.info("mood saved note=%s", SENTINEL)

    output = stream.getvalue()
    assert SENTINEL not in output
    assert "note=[redacted]" in output
    assert json.loads(output)["level"] == "INFO"


def test_sensitive_extra_keys_are_redacted():
    logger, stream = _capture()
    logger.info("journal write", extra={"content": SENTINEL, "q": SENTINEL})

    output = stream.getvalue()
    assert SENTINEL not in output
    assert "[redacted]" in output


def test_email_extra_is_hashed_not_dropped():
    logger, stream = _capture()
    logger.info("invite sent", extra={"email": "mira@example.com"})
    payload = json.loads(stream.getvalue())

    assert payload["email"] != "mira@example.com"
    assert len(payload["email"]) == 12
    assert "mira" not in json.dumps(payload)


def test_token_query_value_is_masked_in_text():
    logger, stream = _capture()
    logger.warning("bad link /api/v1/privacy/export/abc/download/?token=raw-secret-value")

    output = stream.getvalue()
    assert "raw-secret-value" not in output
    assert "token=[redacted]" in output


def test_public_token_path_segment_is_masked():
    logger, stream = _capture()
    logger.info("public open", extra={"path": "/api/v1/public/invitations/abc123token/"})
    payload = json.loads(stream.getvalue())

    assert payload["path"] == "/api/v1/public/invitations/<token>/"


def test_mask_path_drops_query_string():
    assert mask_path("/api/v1/moods/?page=2&q=private") == "/api/v1/moods/"
    assert mask_path("/api/v1/public/support-requests/secret/") == (
        "/api/v1/public/support-requests/<token>/"
    )
    assert mask_path("/api/v1/public/account-deletion/cancel/secret/") == (
        "/api/v1/public/account-deletion/cancel/<token>/"
    )


def test_non_sensitive_fields_survive():
    logger, stream = _capture()
    logger.info("mood saved", extra={"mood_id": "abc", "duration_ms": 12})
    payload = json.loads(stream.getvalue())

    assert payload["mood_id"] == "abc"
    assert payload["duration_ms"] == 12
