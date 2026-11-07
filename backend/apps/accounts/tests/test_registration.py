import pytest
from django.core import mail

from apps.accounts.models import EmailVerificationToken, User
from apps.privacy.models import AuditEvent, ConsentRecord
from apps.profiles.models import UserPreferences, UserProfile

from .conftest import PASSWORD

URL = "/api/v1/auth/register/"


def payload(**overrides):
    data = {
        "email": "Mira@Example.COM",
        "password": PASSWORD,
        "accept_terms": True,
        "accept_privacy": True,
        "timezone": "Europe/Berlin",
        "display_name": "Mira",
    }
    data.update(overrides)
    return data


@pytest.mark.django_db
def test_registration_creates_every_required_row_in_one_transaction(
    anon_client, django_capture_on_commit_callbacks
):
    with django_capture_on_commit_callbacks(execute=True):
        response = anon_client.post(URL, payload(), format="json")

    assert response.status_code == 201
    assert response.data["email"] == "mira@example.com"
    assert response.data["email_verified"] is False
    assert response.data["onboarding_required"] is True
    assert "password" not in response.data

    user = User.objects.get(email="mira@example.com")
    assert user.check_password(PASSWORD)
    assert user.email_verified_at is None
    assert UserProfile.objects.filter(user=user, display_name="Mira").exists()
    assert UserPreferences.objects.filter(user=user).exists()
    consents = ConsentRecord.objects.filter(user=user).order_by("consent_type")
    assert [c.consent_type for c in consents] == ["privacy_policy", "terms_of_service"]
    assert all(c.granted and c.policy_version == "1.0" and c.granted_at for c in consents)
    assert EmailVerificationToken.objects.filter(user=user).count() == 1
    assert AuditEvent.objects.filter(actor=user, event_type="auth.register").exists()

    assert len(mail.outbox) == 1
    message = mail.outbox[0]
    assert message.to == ["mira@example.com"]
    assert "/verify-email/" in message.body
    # The raw token is only in the email, never in the database.
    raw = message.body.split("/verify-email/")[1].split()[0]
    token = EmailVerificationToken.objects.get(user=user)
    assert token.token_hash != raw
    assert raw not in str(token.token_hash)


@pytest.mark.django_db
def test_registration_defaults_display_name_and_timezone(anon_client):
    data = payload(email="quiet.person@example.com")
    data.pop("display_name")
    data.pop("timezone")

    response = anon_client.post(URL, data, format="json")

    assert response.status_code == 201
    profile = UserProfile.objects.get(user__email="quiet.person@example.com")
    assert profile.display_name == "Quiet Person"
    assert profile.timezone == "UTC"


@pytest.mark.django_db
def test_duplicate_email_is_case_insensitive_and_creates_nothing(anon_client):
    assert anon_client.post(URL, payload(), format="json").status_code == 201

    response = anon_client.post(
        URL, payload(email="MIRA@example.com", display_name="Other"), format="json"
    )

    assert response.status_code == 409
    assert response.data["error"]["code"] == "email_in_use"
    assert User.objects.count() == 1


@pytest.mark.django_db
def test_missing_consent_is_rejected_without_writing(anon_client):
    response = anon_client.post(URL, payload(accept_privacy=False), format="json")

    assert response.status_code == 400
    assert response.data["error"]["code"] == "validation_error"
    assert "consents" in response.data["error"]["fields"]
    assert User.objects.count() == 0


@pytest.mark.django_db
def test_weak_or_common_password_is_rejected_with_reason(anon_client):
    response = anon_client.post(URL, payload(password="short"), format="json")

    assert response.status_code == 400
    assert "password" in response.data["error"]["fields"]
    assert User.objects.count() == 0


@pytest.mark.django_db
def test_unknown_field_is_rejected(anon_client):
    response = anon_client.post(URL, payload(accept_everything=True), format="json")

    assert response.status_code == 400
    assert response.data["error"]["code"] == "unknown_field"
    assert "accept_everything" in response.data["error"]["fields"]


@pytest.mark.django_db
def test_invalid_timezone_is_rejected(anon_client):
    response = anon_client.post(URL, payload(timezone="Mars/Olympus"), format="json")

    assert response.status_code == 400
    assert "timezone" in response.data["error"]["fields"]


@pytest.mark.django_db
def test_email_failure_does_not_roll_back_registration(
    anon_client, django_capture_on_commit_callbacks, monkeypatch, caplog
):
    def boom(*args, **kwargs):
        raise RuntimeError("smtp is down")

    monkeypatch.setattr("apps.accounts.services.auth.send_template", boom)

    with django_capture_on_commit_callbacks(execute=True):
        response = anon_client.post(URL, payload(), format="json")

    assert response.status_code == 201
    assert User.objects.filter(email="mira@example.com").exists()
    assert "email_send_failed" in caplog.text
    assert "mira@example.com" not in caplog.text
