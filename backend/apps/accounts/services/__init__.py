"""Authentication services (WF-01 to WF-04)."""

from .auth import (  # noqa: F401
    change_password,
    confirm_email_change,
    confirm_password_reset,
    end_all_sessions,
    end_session,
    normalize_email,
    register_user,
    request_email_change,
    request_password_reset,
    resend_verification,
    session_payload,
    start_session,
    verify_email,
)

__all__ = [
    "change_password",
    "confirm_email_change",
    "confirm_password_reset",
    "end_all_sessions",
    "end_session",
    "normalize_email",
    "register_user",
    "request_email_change",
    "request_password_reset",
    "resend_verification",
    "session_payload",
    "start_session",
    "verify_email",
]
