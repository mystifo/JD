from datetime import timedelta

import pytest
from django.core import mail
from django.utils import timezone
from freezegun import freeze_time

from apps.accounts.constants import EMAIL_CHANGE_TTL
from apps.accounts.models import EmailChangeRequest, User
from apps.accounts.tokens import issue_email_change_request
from apps.privacy.models import AuditEvent

from .conftest import PASSWORD

REQUEST = "/api/v1/auth/email-change/"
CONFIRM = "/api/v1/auth/email-change/confirm/"


@pytest.mark.django_db
def test_email_change_request_sends_two_notices_and_keeps_old_address(
    owner_client, owner, django_capture_on_commit_callbacks
):
    with django_capture_on_commit_callbacks(execute=True):
        response = owner_client.post(
            REQUEST,
            {"new_email": "New@Example.com", "current_password": PASSWORD},
            format="json",
        )

    assert response.status_code == 202
    assert response.data == {"pending": True, "new_email": "n***@example.com"}
    owner.refresh_from_db()
    assert owner.email == "owner@example.com"
    row = EmailChangeRequest.objects.get(user=owner)
    assert row.new_email == "new@example.com"
    assert len(row.token_hash) == 64
    assert sorted(message.to[0] for message in mail.outbox) == [
        "new@example.com",
        "owner@example.com",
    ]
    assert AuditEvent.objects.filter(event_type="auth.email_change_requested").exists()


@pytest.mark.django_db
def test_email_change_requires_the_current_password(owner_client, owner):
    response = owner_client.post(
        REQUEST,
        {"new_email": "new@example.com", "current_password": "nope"},
        format="json",
    )

    assert response.status_code == 400
    assert "current_password" in response.data["error"]["fields"]
    assert EmailChangeRequest.objects.count() == 0


@pytest.mark.django_db
def test_email_change_rejects_an_address_in_use(owner_client, owner, other_user):
    response = owner_client.post(
        REQUEST,
        {"new_email": other_user.email, "current_password": PASSWORD},
        format="json",
    )

    assert response.status_code == 409
    assert response.data["error"]["code"] == "email_in_use"


@pytest.mark.django_db
def test_email_change_rejects_the_current_address(owner_client, owner):
    response = owner_client.post(
        REQUEST,
        {"new_email": owner.email, "current_password": PASSWORD},
        format="json",
    )

    assert response.status_code == 400
    assert "new_email" in response.data["error"]["fields"]


@pytest.mark.django_db
def test_confirming_changes_the_address_and_verifies_it(anon_client, owner):
    raw, row = issue_email_change_request(owner, "fresh@example.com", EMAIL_CHANGE_TTL)

    response = anon_client.post(CONFIRM, {"token": raw}, format="json")

    assert response.status_code == 200
    assert response.data == {"email": "fresh@example.com", "email_verified": True}
    owner.refresh_from_db()
    row.refresh_from_db()
    assert owner.email == "fresh@example.com"
    assert owner.email_verified_at is not None
    assert row.confirmed_at is not None
    assert AuditEvent.objects.filter(event_type="auth.email_changed").exists()


@pytest.mark.django_db
def test_confirming_detects_a_race_for_the_address(anon_client, owner):
    raw, row = issue_email_change_request(owner, "claimed@example.com", EMAIL_CHANGE_TTL)
    User.objects.create_user(email="claimed@example.com", password=PASSWORD)

    response = anon_client.post(CONFIRM, {"token": raw}, format="json")

    assert response.status_code == 409
    assert response.data["error"]["code"] == "email_in_use"
    owner.refresh_from_db()
    assert owner.email == "owner@example.com"


@pytest.mark.django_db
def test_confirmation_token_error_branches(anon_client, owner):
    invalid = anon_client.post(CONFIRM, {"token": "nope"}, format="json")
    assert invalid.status_code == 410
    assert invalid.data["error"]["code"] == "token_invalid"

    raw, row = issue_email_change_request(owner, "first@example.com", EMAIL_CHANGE_TTL)
    with freeze_time(timezone.now() + timedelta(hours=3)):
        expired = anon_client.post(CONFIRM, {"token": raw}, format="json")
    assert expired.status_code == 410
    assert expired.data["error"]["code"] == "token_expired"
    EmailChangeRequest.objects.filter(pk=row.pk).delete()

    raw2, row2 = issue_email_change_request(owner, "second@example.com", EMAIL_CHANGE_TTL)
    assert anon_client.post(CONFIRM, {"token": raw2}, format="json").status_code == 200
    used = anon_client.post(CONFIRM, {"token": raw2}, format="json")
    assert used.status_code == 409
    assert used.data["error"]["code"] == "token_used"


@pytest.mark.django_db
def test_email_change_is_throttled_per_day(owner_client, owner):
    for index in range(3):
        response = owner_client.post(
            REQUEST,
            {"new_email": f"new{index}@example.com", "current_password": PASSWORD},
            format="json",
        )
        assert response.status_code == 202

    response = owner_client.post(
        REQUEST,
        {"new_email": "last@example.com", "current_password": PASSWORD},
        format="json",
    )
    assert response.status_code == 429
