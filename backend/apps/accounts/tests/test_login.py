from datetime import timedelta

import pytest
from django.core.cache import cache
from django.utils import timezone

from apps.accounts.models import User
from apps.privacy.models import AuditEvent

from .conftest import PASSWORD

URL = "/api/v1/auth/login/"


def login(client, email="mira@example.com", password=PASSWORD):
    return client.post(URL, {"email": email, "password": password}, format="json")


@pytest.mark.django_db
def test_login_sets_session_and_returns_verified_flag(anon_client, registered):
    response = login(anon_client)

    assert response.status_code == 200
    assert response.data["user"]["email"] == "mira@example.com"
    assert response.data["user"]["email_verified"] is False
    assert response.data["onboarding_required"] is True
    assert response.data["preferences"] == {"theme": "system", "reduced_motion": False}
    assert "sessionid" in response.cookies
    assert AuditEvent.objects.filter(event_type="auth.login").exists()

    session = anon_client.get("/api/v1/auth/session/")
    assert session.status_code == 200
    assert session.data["user"]["display_name"] == "Mira"


@pytest.mark.django_db
def test_wrong_password_and_unknown_email_are_indistinguishable(anon_client, registered):
    wrong = login(anon_client, password="not-the-password")
    unknown = login(anon_client, email="nobody@example.com", password="not-the-password")

    assert wrong.status_code == unknown.status_code == 401
    assert wrong.data["error"]["code"] == unknown.data["error"]["code"] == "invalid_credentials"
    assert wrong.data["error"]["message"] == unknown.data["error"]["message"]
    assert "sessionid" not in wrong.cookies
    assert AuditEvent.objects.filter(event_type="auth.login_failed").count() == 2


@pytest.mark.django_db
def test_ten_failures_lock_the_account_for_fifteen_minutes(anon_client, verified_user):
    for _ in range(10):
        response = login(anon_client, email=verified_user.email, password="wrong-password")
        assert response.status_code == 401
        cache.clear()

    verified_user.refresh_from_db()
    assert verified_user.failed_login_count == 10
    assert verified_user.locked_until is not None

    locked = login(anon_client, email=verified_user.email)
    assert locked.status_code == 423
    assert locked.data["error"]["code"] == "account_locked"
    assert locked.data["error"]["fields"]["retry_after_seconds"] > 0
    assert AuditEvent.objects.filter(event_type="auth.lockout").exists()


@pytest.mark.django_db
def test_successful_login_resets_failure_counter(anon_client, verified_user):
    User.objects.filter(pk=verified_user.pk).update(failed_login_count=4)

    response = login(anon_client, email=verified_user.email)

    assert response.status_code == 200
    verified_user.refresh_from_db()
    assert verified_user.failed_login_count == 0
    assert verified_user.locked_until is None


@pytest.mark.django_db
def test_expired_lockout_starts_a_fresh_run(anon_client, verified_user):
    User.objects.filter(pk=verified_user.pk).update(
        failed_login_count=10,
        locked_until=timezone.now() - timedelta(seconds=1),
    )

    response = login(anon_client, email=verified_user.email)

    assert response.status_code == 200
    verified_user.refresh_from_db()
    assert verified_user.failed_login_count == 0


@pytest.mark.django_db
def test_inactive_account_is_reported_after_the_password_is_checked(anon_client, verified_user):
    User.objects.filter(pk=verified_user.pk).update(is_active=False)

    response = login(anon_client, email=verified_user.email)

    assert response.status_code == 403
    assert response.data["error"]["code"] == "deletion_pending"
    assert "sessionid" not in response.cookies
