import pytest
from django.http import Http404
from rest_framework import exceptions as drf_exceptions
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from common.exceptions import (
    NotFound,
    PermissionDenied,
    TokenExpired,
    ValidationFailure,
    api_exception_handler,
)


def _context():
    request = APIRequestFactory().get("/api/v1/example/")
    request.request_id = "0f0b0c7e-6a1a-4c0e-9c1e-3f0f2f8a1b22"
    return {"request": request, "view": None}


def test_domain_error_uses_the_documented_envelope():
    exc = ValidationFailure("Some fields need attention.", fields={"intensity": ["Too low."]})
    response = api_exception_handler(exc, _context())

    assert response.status_code == 400
    assert response.data == {
        "error": {
            "code": "validation_error",
            "message": "Some fields need attention.",
            "fields": {"intensity": ["Too low."]},
            "request_id": "0f0b0c7e-6a1a-4c0e-9c1e-3f0f2f8a1b22",
        }
    }


def test_domain_error_status_and_code_are_independent():
    response = api_exception_handler(TokenExpired("That link has expired."), _context())
    assert response.status_code == 410
    assert response.data["error"]["code"] == "token_expired"


def test_drf_validation_error_maps_to_validation_error():
    exc = drf_exceptions.ValidationError({"email": ["Enter a valid email address."]})
    response = api_exception_handler(exc, _context())

    assert response.status_code == 400
    assert response.data["error"]["code"] == "validation_error"
    assert response.data["error"]["fields"] == {"email": ["Enter a valid email address."]}
    assert response.data["error"]["message"] == "Some fields need attention."


def test_http404_maps_to_not_found_never_forbidden():
    response = api_exception_handler(Http404(), _context())
    assert response.status_code == 404
    assert response.data["error"]["code"] == "not_found"


def test_permission_denied_keeps_specific_code():
    exc = drf_exceptions.PermissionDenied(
        detail="Verify your email to use this part of HerSpace.",
        code="email_not_verified",
    )
    response = api_exception_handler(exc, _context())

    assert response.status_code == 403
    assert response.data["error"]["code"] == "email_not_verified"
    assert "Verify your email" in response.data["error"]["message"]


def test_not_authenticated_maps_to_401():
    response = api_exception_handler(drf_exceptions.NotAuthenticated(), _context())
    assert response.status_code == 401
    assert response.data["error"]["code"] == "authentication_required"


def test_unhandled_exception_hides_internals():
    response = api_exception_handler(RuntimeError("secret detail"), _context())

    assert response.status_code == 500
    assert response.data["error"]["code"] == "server_error"
    assert "secret detail" not in str(response.data)
    assert response.data["error"]["request_id"] == "0f0b0c7e-6a1a-4c0e-9c1e-3f0f2f8a1b22"


@pytest.mark.parametrize(
    "exc,status,code",
    [
        (NotFound("gone"), 404, "not_found"),
        (PermissionDenied("no"), 403, "permission_denied"),
    ],
)
def test_common_domain_errors(exc, status, code):
    response = api_exception_handler(exc, _context())
    assert response.status_code == status
    assert response.data["error"]["code"] == code


def test_request_id_is_optional():
    request = Request(APIRequestFactory().get("/"))
    response = api_exception_handler(ValidationFailure("nope"), {"request": request, "view": None})
    assert response.data["error"]["request_id"] is None
