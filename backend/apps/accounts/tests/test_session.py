import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User

from .conftest import PASSWORD


def login(client, email, password=PASSWORD):
    return client.post("/api/v1/auth/login/", {"email": email, "password": password}, format="json")


@pytest.mark.django_db
def test_session_requires_authentication(anon_client):
    response = anon_client.get("/api/v1/auth/session/")

    assert response.status_code == 401
    assert response.data["error"]["code"] == "authentication_required"


@pytest.mark.django_db
def test_csrf_endpoint_sets_readable_cookie(anon_client):
    response = anon_client.get("/api/v1/auth/csrf/")

    assert response.status_code == 204
    assert "csrftoken" in response.cookies


@pytest.mark.django_db
def test_session_version_mismatch_ends_the_session(verified_user):
    client = APIClient()
    assert login(client, verified_user.email).status_code == 200
    assert client.get("/api/v1/auth/session/").status_code == 200

    User.objects.filter(pk=verified_user.pk).update(session_version=1)

    response = client.get("/api/v1/auth/session/")
    assert response.status_code == 401
    assert response.data["error"]["code"] == "authentication_required"


@pytest.mark.django_db
def test_unverified_user_can_read_session_but_not_private_data(anon_client, registered):
    assert login(anon_client, registered.email).status_code == 200

    session = anon_client.get("/api/v1/auth/session/")
    assert session.status_code == 200
    assert session.data["user"]["email_verified"] is False

    private = anon_client.get("/api/v1/profile/")
    assert private.status_code == 403
    assert private.data["error"]["code"] == "email_not_verified"
