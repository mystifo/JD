from datetime import timedelta

import pytest
from django.utils import timezone
from freezegun import freeze_time
from rest_framework.test import APIClient

from apps.accounts.constants import EMAIL_VERIFICATION_TTL
from apps.accounts.models import EmailVerificationToken
from apps.accounts.tokens import issue_user_token
from apps.privacy.models import AuditEvent

from .conftest import PASSWORD

VERIFY = "/api/v1/auth/verify-email/"
RESEND = "/api/v1/auth/verify-email/resend/"


def token_for(user):
    raw, row = issue_user_token(EmailVerificationToken, user, EMAIL_VERIFICATION_TTL)
    return raw, row


@pytest.mark.django_db
def test_valid_token_verifies_and_marks_it_used(anon_client, registered):
    raw, row = token_for(registered)

    response = anon_client.post(VERIFY, {"token": raw}, format="json")

    assert response.status_code == 200
    assert response.data == {"email_verified": True}
    registered.refresh_from_db()
    row.refresh_from_db()
    assert registered.email_verified_at is not None
    assert row.used_at is not None
    assert AuditEvent.objects.filter(event_type="auth.email_verified").exists()


@pytest.mark.django_db
def test_reused_token_returns_conflict_and_changes_nothing(anon_client, registered):
    raw, _ = token_for(registered)
    assert anon_client.post(VERIFY, {"token": raw}, format="json").status_code == 200
    registered.refresh_from_db()
    first_verified_at = registered.email_verified_at

    response = anon_client.post(VERIFY, {"token": raw}, format="json")

    assert response.status_code == 409
    assert response.data["error"]["code"] == "token_used"
    registered.refresh_from_db()
    assert registered.email_verified_at == first_verified_at


@pytest.mark.django_db
def test_expired_token_returns_gone(anon_client, registered):
    raw, row = token_for(registered)

    with freeze_time(timezone.now() + timedelta(hours=25)):
        response = anon_client.post(VERIFY, {"token": raw}, format="json")

    assert response.status_code == 410
    assert response.data["error"]["code"] == "token_expired"


@pytest.mark.django_db
def test_unknown_token_returns_gone(anon_client):
    response = anon_client.post(VERIFY, {"token": "not-a-real-token"}, format="json")

    assert response.status_code == 410
    assert response.data["error"]["code"] == "token_invalid"


@pytest.mark.django_db
def test_resend_sends_one_email_and_replaces_old_tokens(
    anon_client, registered, django_capture_on_commit_callbacks
):
    client = APIClient()
    client.post(
        "/api/v1/auth/login/",
        {"email": registered.email, "password": PASSWORD},
        format="json",
    )
    old_count = EmailVerificationToken.objects.filter(user=registered).count()

    with django_capture_on_commit_callbacks(execute=True) as callbacks:
        response = client.post(RESEND)

    assert response.status_code == 202
    assert response.data == {"sent": True}
    assert len(callbacks) == 1
    assert EmailVerificationToken.objects.filter(user=registered).count() == old_count


@pytest.mark.django_db
def test_resend_is_a_no_op_for_a_verified_user(owner_client, owner):
    response = owner_client.post(RESEND)

    assert response.status_code == 200
    assert response.data == {"sent": False}


@pytest.mark.django_db
def test_resend_throttle(anon_client, registered, django_capture_on_commit_callbacks):
    client = APIClient()
    client.post(
        "/api/v1/auth/login/",
        {"email": registered.email, "password": PASSWORD},
        format="json",
    )
    for _ in range(3):
        assert client.post(RESEND).status_code == 202

    assert client.post(RESEND).status_code == 429
