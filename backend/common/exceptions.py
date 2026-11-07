"""Domain exceptions and the single DRF exception handler.

The envelope is defined in `docs/api-documentation.md` §1.5:

    {"error": {"code": ..., "message": ..., "fields": ..., "request_id": ...}}
"""

import logging

from django.http import Http404
from rest_framework import exceptions as drf_exceptions
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)


class DomainError(Exception):
    """Base class for service-layer failures with an API-safe message."""

    code = "domain_error"
    status = status.HTTP_400_BAD_REQUEST

    def __init__(self, message, *, fields=None, code=None):
        super().__init__(message)
        self.message = message
        self.fields = fields or {}
        if code is not None:
            self.code = code


class ValidationFailure(DomainError):
    code = "validation_error"
    status = status.HTTP_400_BAD_REQUEST


class UnknownField(DomainError):
    code = "unknown_field"
    status = status.HTTP_400_BAD_REQUEST


class ConsentRequired(DomainError):
    code = "consent_required"
    status = status.HTTP_400_BAD_REQUEST


class Conflict(DomainError):
    code = "conflict"
    status = status.HTTP_409_CONFLICT


class NotFound(DomainError):
    code = "not_found"
    status = status.HTTP_404_NOT_FOUND


class PermissionDenied(DomainError):
    code = "permission_denied"
    status = status.HTTP_403_FORBIDDEN


class TokenExpired(DomainError):
    code = "token_expired"
    status = status.HTTP_410_GONE


class TokenInvalid(DomainError):
    code = "token_invalid"
    status = status.HTTP_410_GONE


class TokenUsed(DomainError):
    code = "token_used"
    status = status.HTTP_409_CONFLICT


class RateLimited(DomainError):
    code = "rate_limited"
    status = status.HTTP_429_TOO_MANY_REQUESTS


class InvalidCredentials(DomainError):
    code = "invalid_credentials"
    status = status.HTTP_401_UNAUTHORIZED


class EmailInUse(DomainError):
    code = "email_in_use"
    status = status.HTTP_409_CONFLICT


class DeletionPending(DomainError):
    code = "deletion_pending"
    status = status.HTTP_403_FORBIDDEN


class Locked(DomainError):
    code = "account_locked"
    status = status.HTTP_423_LOCKED


def _request_id(request):
    return getattr(request, "request_id", None)


def _envelope(code, message, *, fields=None, request_id=None):
    body = {"code": code, "message": message, "request_id": request_id}
    if fields:
        body["fields"] = fields
    return {"error": body}


_STATUS_CODES = {
    status.HTTP_400_BAD_REQUEST: "validation_error",
    status.HTTP_401_UNAUTHORIZED: "authentication_required",
    status.HTTP_403_FORBIDDEN: "permission_denied",
    status.HTTP_404_NOT_FOUND: "not_found",
    status.HTTP_405_METHOD_NOT_ALLOWED: "method_not_allowed",
    status.HTTP_409_CONFLICT: "conflict",
    status.HTTP_410_GONE: "token_expired",
    status.HTTP_415_UNSUPPORTED_MEDIA_TYPE: "unsupported_media_type",
    status.HTTP_423_LOCKED: "account_locked",
    status.HTTP_429_TOO_MANY_REQUESTS: "rate_limited",
}


def _specific_code(exc, fallback):
    detail = getattr(exc, "detail", None)
    code = getattr(detail, "code", None)
    if isinstance(code, str) and code.isidentifier():
        return code
    return fallback


def api_exception_handler(exc, context):
    request = context.get("request") if context else None
    request_id = _request_id(request)

    if isinstance(exc, DomainError):
        response = Response(
            _envelope(exc.code, exc.message, fields=exc.fields, request_id=request_id),
            status=exc.status,
        )
        if exc.status == status.HTTP_429_TOO_MANY_REQUESTS:
            retry_after = exc.fields.get("retry_after_seconds")
            if retry_after:
                response["Retry-After"] = str(int(retry_after))
        return response

    if isinstance(exc, Http404):
        exc = drf_exceptions.NotFound()

    response = drf_exception_handler(exc, context)

    if response is None:
        logger.exception("unhandled_api_error", extra={"request_id": request_id})
        return Response(
            _envelope(
                "server_error",
                "Something went wrong. Please try again.",
                request_id=request_id,
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    code = _specific_code(exc, _STATUS_CODES.get(response.status_code, "server_error"))
    fields = None
    if isinstance(exc, drf_exceptions.ValidationError):
        code = "validation_error"
        fields = response.data
    elif isinstance(exc, drf_exceptions.ParseError):
        code = "validation_error"
    elif isinstance(exc, (drf_exceptions.NotAuthenticated, drf_exceptions.AuthenticationFailed)):
        code = "authentication_required"
    elif isinstance(exc, drf_exceptions.Throttled):
        code = "rate_limited"

    message = _safe_message(exc, code)
    response.data = _envelope(code, message, fields=fields, request_id=request_id)
    if isinstance(exc, drf_exceptions.NotAuthenticated):
        # DRF downgrades a missing session to 403 when the authenticator has no
        # WWW-Authenticate header. The API contract is always 401 for no session.
        response.status_code = status.HTTP_401_UNAUTHORIZED
    if isinstance(exc, drf_exceptions.Throttled) and getattr(exc, "wait", None):
        response["Retry-After"] = str(int(exc.wait))
    return response


def _safe_message(exc, code):
    messages = {
        "validation_error": "Some fields need attention.",
        "authentication_required": "Sign in to continue.",
        "permission_denied": "You don't have access to that.",
        "not_found": "We couldn't find that.",
        "method_not_allowed": "That method isn't supported here.",
        "unsupported_media_type": "Send JSON with Content-Type: application/json.",
        "rate_limited": "Too many attempts. Please wait a moment and try again.",
        "server_error": "Something went wrong. Please try again.",
    }
    if code in messages:
        return messages[code]
    detail = getattr(exc, "detail", None)
    if isinstance(detail, str):
        return detail
    return "Something needs your attention."
