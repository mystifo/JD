from datetime import date, timedelta

import pytest

from apps.accounts.models import User
from apps.privacy.models import AuditEvent
from apps.profiles.models import UserProfile
from apps.profiles.services import profile_for


@pytest.mark.django_db
def test_profile_reads_owner_data(owner_client, owner):
    profile = profile_for(owner)
    profile.display_name = "Mira"
    profile.pronouns = "she/her"
    profile.timezone = "Europe/Berlin"
    profile.save()

    response = owner_client.get("/api/v1/profile/")

    assert response.status_code == 200
    assert response.data["id"] == str(owner.pk)
    assert response.data["email"] == "owner@example.com"
    assert response.data["email_verified"] is True
    assert response.data["display_name"] == "Mira"
    assert response.data["pronouns"] == "she/her"
    assert response.data["locale"] == "en"


@pytest.mark.django_db
def test_profile_update_records_only_changed_keys(owner_client, owner):
    response = owner_client.patch(
        "/api/v1/profile/",
        {
            "display_name": "Mira",
            "pronouns": "she/her",
            "bio": "A quiet bio.",
            "timezone": "Europe/Berlin",
            "date_of_birth": "1994-04-12",
        },
        format="json",
    )

    assert response.status_code == 200
    assert response.data["timezone"] == "Europe/Berlin"
    assert response.data["bio"] == "A quiet bio."
    event = AuditEvent.objects.get(event_type="profile.updated")
    assert event.metadata == {
        "changed": ["bio", "date_of_birth", "display_name", "pronouns", "timezone"]
    }
    assert "Mira" not in str(event.metadata)
    assert "quiet bio" not in str(event.metadata)


@pytest.mark.django_db
def test_profile_rejects_an_invalid_timezone(owner_client):
    response = owner_client.patch("/api/v1/profile/", {"timezone": "Mars/Olympus"}, format="json")

    assert response.status_code == 400
    assert response.data["error"]["code"] == "invalid_timezone"
    assert "timezone" in response.data["error"]["fields"]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "payload,field",
    [
        ({"display_name": ""}, "display_name"),
        ({"bio": "x" * 281}, "bio"),
        ({"pronouns": "x" * 41}, "pronouns"),
        ({"locale": "fr"}, "locale"),
        ({"date_of_birth": (date.today() + timedelta(days=1)).isoformat()}, "date_of_birth"),
        ({"date_of_birth": (date.today() - timedelta(days=365 * 10)).isoformat()}, "date_of_birth"),
    ],
)
def test_profile_field_validation(owner_client, payload, field):
    response = owner_client.patch("/api/v1/profile/", payload, format="json")

    assert response.status_code == 400
    assert field in response.data["error"]["fields"]


@pytest.mark.django_db
def test_profile_cannot_change_email(owner_client):
    response = owner_client.patch("/api/v1/profile/", {"email": "new@example.com"}, format="json")

    assert response.status_code == 400
    assert response.data["error"]["code"] == "unknown_field"


@pytest.mark.django_db
def test_profile_requires_a_verified_email(db):
    user = User.objects.create_user(email="unverified@example.com", password="irrelevant")
    from rest_framework.test import APIClient

    client = APIClient()
    client.force_authenticate(user)
    response = client.get("/api/v1/profile/")

    assert response.status_code == 403
    assert response.data["error"]["code"] == "email_not_verified"
    assert UserProfile.objects.filter(user=user).count() == 0


@pytest.mark.django_db
def test_profile_is_created_with_defaults_on_first_read(owner_client, owner):
    response = owner_client.get("/api/v1/profile/")

    assert response.status_code == 200
    assert response.data["display_name"] == "Owner"
    assert response.data["timezone"] == "UTC"
    assert response.data["bio"] is None
    assert response.data["onboarding_completed_at"] is None
