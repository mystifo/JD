"""Log redaction and JSON formatting.

Invariants (security.md §9):
- request/response bodies are never logged;
- keys such as `content`, `note`, `message`, `snapshot`, `email`, `phone`,
  `token`, `password`, `q`, and `search` are dropped or hashed;
- public token path segments and `token=` query values are masked.
"""

import json
import logging
import re
from contextvars import ContextVar
from datetime import UTC, datetime

from common.crypto import email_fingerprint

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

REDACTED = "[redacted]"

SENSITIVE_KEYS = frozenset(
    {
        "password",
        "token",
        "authorization",
        "cookie",
        "csrftoken",
        "csrf",
        "content",
        "note",
        "message",
        "response_note",
        "snapshot",
        "phone",
        "q",
        "search",
        "raw_token",
        "secret",
    }
)
EMAIL_KEYS = frozenset({"email", "to", "to_email", "recipient"})

_TOKEN_QUERY_RE = re.compile(r"(token=)([^&\s\"']+)", re.IGNORECASE)
_QUERY_STRING_RE = re.compile(r"\?[^\s\"']*")
_PUBLIC_TOKEN_PATH_RE = re.compile(
    r"(/api/v1/public/(?:invitations|support-requests|account-deletion/cancel)/)([^/\s?]+)",
    re.IGNORECASE,
)
_DOWNLOAD_TOKEN_PATH_RE = re.compile(r"(/download/)([^/\s?]+)", re.IGNORECASE)
_KEY_VALUE_RE = re.compile(
    r"\b(" + "|".join(sorted(SENSITIVE_KEYS)) + r")=([^\s,;\"']+)",
    re.IGNORECASE,
)

RESERVED_LOG_KEYS = frozenset(
    {
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
        "taskName",
        "message",
        "asctime",
    }
)


def mask_path(path: str | None) -> str | None:
    """Mask public token segments; drop the query string entirely."""
    if not path:
        return path
    path = _PUBLIC_TOKEN_PATH_RE.sub(r"\1<token>", path)
    path = _DOWNLOAD_TOKEN_PATH_RE.sub(r"\1<token>", path)
    path = _QUERY_STRING_RE.sub("", path)
    return path


def redact_text(value: str) -> str:
    value = _TOKEN_QUERY_RE.sub(r"\1[redacted]", value)
    value = _PUBLIC_TOKEN_PATH_RE.sub(r"\1<token>", value)
    value = _DOWNLOAD_TOKEN_PATH_RE.sub(r"\1<token>", value)
    return _KEY_VALUE_RE.sub(lambda m: f"{m.group(1)}={REDACTED}", value)


def redact_value(value):
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, dict):
        return {
            key: (
                REDACTED
                if str(key).lower() in SENSITIVE_KEYS
                else (
                    _hash_email(value[key])
                    if str(key).lower() in EMAIL_KEYS
                    else redact_value(item)
                )
            )
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return type(value)(redact_value(item) for item in value)
    return value


def _hash_email(value):
    if isinstance(value, str):
        return email_fingerprint(value)
    if isinstance(value, (list, tuple)):
        return type(value)(_hash_email(item) for item in value)
    return REDACTED


class RedactSensitiveFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        # Resolve placeholders first so redaction cannot desynchronise msg/args.
        record.msg = redact_value(record.getMessage())
        record.args = ()

        for key, value in list(record.__dict__.items()):
            lowered = key.lower()
            if lowered in SENSITIVE_KEYS:
                record.__dict__[key] = REDACTED
            elif lowered in EMAIL_KEYS:
                record.__dict__[key] = _hash_email(value)
            elif key == "path":
                record.__dict__[key] = mask_path(str(value))
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.fromtimestamp(record.created, tz=UTC).isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_var.get(),
        }
        for key, value in record.__dict__.items():
            if key in RESERVED_LOG_KEYS or key.startswith("_"):
                continue
            if key in payload:
                continue
            payload[key] = value

        if record.exc_info:
            payload["exc_type"] = record.exc_info[0].__name__ if record.exc_info[0] else None
            payload["exc_message"] = str(record.exc_info[1]) if record.exc_info[1] else None
            payload["traceback"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str, ensure_ascii=False)
