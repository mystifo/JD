"""Structured JSON logging with a redaction filter on every handler."""

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"redact": {"()": "common.logging_filters.RedactSensitiveFilter"}},
    "formatters": {"json": {"()": "common.logging_filters.JsonFormatter"}},
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "filters": ["redact"],
        }
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django.request": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "django.security": {"handlers": ["console"], "level": "WARNING", "propagate": False},
    },
}
