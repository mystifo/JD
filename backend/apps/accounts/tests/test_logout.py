import pytest
from rest_framework.test import APIClient

from apps.notifications.models import Notification
from apps.privacy.models import AuditEvent

from .conftest import PASSWORD


def login(client, email, password=PASSWORD):
    return client.post("/api/v1/auth/login/", {"email": email, "password": password}, format="json")


@pytest.mark.django_db
def test_logout_is_idempotent_and_destroys_the_session(anon_client, registered):
    assert login(anon_client, registered.email).status_code == 200
    assert anon_client.get("/api/v1/auth/session/").status_code == 200

    assert anon_client.post("/api/v1/auth/logout/").status_code == 204
    assert anon_client.get("/api/v1/auth/session/").status_code == 401
    # Already anonymous: still 204.
    assert anon_client.post("/api/v1/auth/logout/").status_code == 204


@pytest.mark.django_db
def test_logout_all_keeps_current_session_and_ends_others(verified_user):
    first = APIClient()
    second = APIClient()
    assert login(first, verified_user.email).status_code == 200
    assert login(second, verified_user.email).status_code == 200

    response = first.post("/api/v1/auth/logout-all/")

    assert response.status_code == 204
    verified_user.refresh_from_db()
    assert verified_user.session_version == 1
    assert first.get("/api/v1/auth/session/").status_code == 200
    assert second.get("/api/v1/auth/session/").status_code == 401
    notification = Notification.objects.get(user=verified_user, category="security_alert")
    assert notification.title == "You were signed out on other devices"
    assert notification.link_path == "/app/settings/security"
    assert AuditEvent.objects.filter(event_type="auth.logout_all").exists()
