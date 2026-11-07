from datetime import timedelta

import pytest
from django.core import mail
from django.utils import timezone
from freezegun import freeze_time
from rest_framework.test import APIClient

from apps.accounts.constants import PASSWORD_RESET_TTL
from apps.accounts.models import PasswordResetToken
from apps.accounts.tokens import issue_user_token
from apps.notifications.models import Notification
from apps.privacy.models import AuditEvent

from .conftest import NEW_PASSWORD, PASSWORD

RESET = "/api/v1/auth/password-reset/"
CONFIRM = "/api/v1/auth/password-reset/confirm/"
CHANGE = "/api/v1/auth/password-change/"


def login(client, email, password=PASSWORD):
    return client.post("/api/v1/auth/login/", {"email": email, "password": password}, format="json")


def reset_token(user):
    return issue_user_token(PasswordResetToken, user, PASSWORD_RESET_TTL)


@pytest.mark.django_db
def test_reset_request_is_identical_for_known_and_unknown_addresses(
    anon_client, django_capture_on_commit_callbacks, verified_user
):
    known = anon_client.post(RESET, {"email": verified_user.email}, format="json")
    unknown = anon_client.post(RESET, {"email": "nobody@example.com"}, format="json")

    assert known.status_code == unknown.status_code == 202
    assert known.data == unknown.data
    assert known.data["message"].startswith("If that address has an account")

    # Only the real account queues a message.
    with django_capture_on_commit_callbacks(execute=True):
        anon_client.post(RESET, {"email": verified_user.email}, format="json")
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [verified_user.email]


@pytest.mark.django_db
def test_reset_token_is_stored_only_as_a_hash(anon_client, verified_user):
    _, row = reset_token(verified_user)

    assert len(row.token_hash) == 64
    assert PasswordResetToken.objects.filter(token_hash=row.token_hash).exists()


@pytest.mark.django_db
def test_reset_confirm_changes_password_and_ends_all_sessions(anon_client, verified_user):
    client = APIClient()
    assert login(client, verified_user.email).status_code == 200
    raw, row = reset_token(verified_user)

    response = anon_client.post(
        CONFIRM, {"token": raw, "new_password": NEW_PASSWORD}, format="json"
    )

    assert response.status_code == 200
    assert response.data == {"password_changed": True}
    verified_user.refresh_from_db()
    row.refresh_from_db()
    assert verified_user.check_password(NEW_PASSWORD)
    assert verified_user.session_version == 1
    assert row.used_at is not None
    assert Notification.objects.filter(
        user=verified_user, category="security_alert", title="Your password was reset"
    ).exists()
    assert AuditEvent.objects.filter(event_type="auth.password_reset_completed").exists()
    # The old session is gone.
    assert client.get("/api/v1/auth/session/").status_code == 401


@pytest.mark.django_db
def test_reset_confirm_rejects_expired_used_invalid_and_stale_tokens(anon_client, verified_user):
    raw, row = reset_token(verified_user)
    with freeze_time(timezone.now() + timedelta(minutes=61)):
        expired = anon_client.post(
            CONFIRM, {"token": raw, "new_password": NEW_PASSWORD}, format="json"
        )
    assert expired.status_code == 410
    assert expired.data["error"]["code"] == "token_expired"

    raw2, row2 = reset_token(verified_user)
    assert (
        anon_client.post(
            CONFIRM, {"token": raw2, "new_password": NEW_PASSWORD}, format="json"
        ).status_code
        == 200
    )
    used = anon_client.post(CONFIRM, {"token": raw2, "new_password": NEW_PASSWORD}, format="json")
    assert used.status_code == 409
    assert used.data["error"]["code"] == "token_used"

    invalid = anon_client.post(
        CONFIRM, {"token": "nope", "new_password": NEW_PASSWORD}, format="json"
    )
    assert invalid.status_code == 410
    assert invalid.data["error"]["code"] == "token_invalid"

    raw3, row3 = reset_token(verified_user)
    PasswordResetToken.objects.filter(pk=row3.pk).update(
        created_at=verified_user.password_changed_at - timedelta(seconds=1)
    )
    stale = anon_client.post(CONFIRM, {"token": raw3, "new_password": NEW_PASSWORD}, format="json")
    assert stale.status_code == 410
    assert stale.data["error"]["code"] == "token_invalid"


@pytest.mark.django_db
def test_reset_confirm_validates_the_new_password(anon_client, verified_user):
    raw, _ = reset_token(verified_user)

    response = anon_client.post(CONFIRM, {"token": raw, "new_password": "short"}, format="json")

    assert response.status_code == 400
    assert "new_password" in response.data["error"]["fields"]
    verified_user.refresh_from_db()
    assert verified_user.check_password(PASSWORD)


@pytest.mark.django_db
def test_any_password_change_invalidates_an_outstanding_reset_token(verified_user):
    raw, _ = reset_token(verified_user)
    verified_user.set_password(NEW_PASSWORD)
    verified_user.password_changed_at = timezone.now()
    verified_user.save(update_fields=["password", "password_changed_at", "updated_at"])

    from apps.accounts.services import confirm_password_reset

    with pytest.raises(Exception) as excinfo:
        confirm_password_reset(raw, "another-long-password-77")
    assert excinfo.value.code == "token_invalid"


@pytest.mark.django_db
def test_password_change_keeps_current_session_and_ends_other_sessions(verified_user):
    first = APIClient()
    second = APIClient()
    assert login(first, verified_user.email).status_code == 200
    assert login(second, verified_user.email).status_code == 200

    response = first.post(
        CHANGE,
        {"current_password": PASSWORD, "new_password": NEW_PASSWORD},
        format="json",
    )

    assert response.status_code == 200
    verified_user.refresh_from_db()
    assert verified_user.check_password(NEW_PASSWORD)
    assert first.get("/api/v1/auth/session/").status_code == 200
    assert second.get("/api/v1/auth/session/").status_code == 401
    assert Notification.objects.filter(
        user=verified_user, title="Your password was changed"
    ).exists()
    assert AuditEvent.objects.filter(event_type="auth.password_changed").exists()


@pytest.mark.django_db
def test_password_change_rejects_wrong_current_and_reused_password(owner_client, owner):
    wrong = owner_client.post(
        CHANGE,
        {"current_password": "wrong-password", "new_password": NEW_PASSWORD},
        format="json",
    )
    assert wrong.status_code == 400
    assert "current_password" in wrong.data["error"]["fields"]

    reused = owner_client.post(
        CHANGE,
        {"current_password": PASSWORD, "new_password": PASSWORD},
        format="json",
    )
    assert reused.status_code == 400
    assert "new_password" in reused.data["error"]["fields"]
    owner.refresh_from_db()
    assert owner.check_password(PASSWORD)


@pytest.mark.django_db
def test_reset_request_throttles_per_address(anon_client, verified_user):
    for _ in range(3):
        assert (
            anon_client.post(RESET, {"email": verified_user.email}, format="json").status_code
            == 202
        )

    response = anon_client.post(RESET, {"email": verified_user.email}, format="json")

    assert response.status_code == 429
    assert response.data["error"]["code"] == "rate_limited"
