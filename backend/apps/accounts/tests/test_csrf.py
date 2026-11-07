import pytest
from rest_framework.test import APIClient

from .conftest import PASSWORD


def payload():
    return {
        "email": "csrf@example.com",
        "password": PASSWORD,
        "accept_terms": True,
        "accept_privacy": True,
        "timezone": "UTC",
    }


@pytest.mark.django_db
def test_public_unsafe_request_without_csrf_token_is_rejected():
    client = APIClient(enforce_csrf_checks=True)

    response = client.post("/api/v1/auth/register/", payload(), format="json")

    assert response.status_code == 403
    assert response.data["error"]["code"] == "permission_denied"


@pytest.mark.django_db
def test_csrf_cookie_unlocks_unsafe_requests(django_capture_on_commit_callbacks):
    client = APIClient(enforce_csrf_checks=True)
    assert client.get("/api/v1/auth/csrf/").status_code == 204
    token = client.cookies["csrftoken"].value

    with django_capture_on_commit_callbacks(execute=True):
        response = client.post(
            "/api/v1/auth/register/",
            payload(),
            format="json",
            HTTP_X_CSRFTOKEN=token,
        )

    assert response.status_code == 201


@pytest.mark.django_db
def test_safe_methods_do_not_require_csrf():
    client = APIClient(enforce_csrf_checks=True)

    assert client.get("/api/v1/health/").status_code == 200
