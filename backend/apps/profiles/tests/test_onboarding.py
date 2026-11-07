import pytest

from apps.accounts.models import User
from apps.privacy.models import AuditEvent, ConsentRecord
from apps.profiles.services import profile_for


@pytest.mark.django_db
def test_onboarding_requires_acknowledgement(owner_client, owner):
    response = owner_client.post(
        "/api/v1/onboarding/complete/", {"privacy_acknowledged": False}, format="json"
    )

    assert response.status_code == 400
    assert response.data["error"]["code"] == "consent_required"
    assert profile_for(owner).onboarding_completed_at is None


@pytest.mark.django_db
def test_onboarding_completion_is_idempotent(owner_client, owner):
    first = owner_client.post(
        "/api/v1/onboarding/complete/", {"privacy_acknowledged": True}, format="json"
    )

    assert first.status_code == 200
    completed_at = first.data["onboarding_completed_at"]
    assert completed_at is not None
    assert (
        ConsentRecord.objects.filter(
            user=owner, consent_type="wellness_disclaimer", granted=True
        ).count()
        == 1
    )
    assert AuditEvent.objects.filter(event_type="onboarding.completed").count() == 1

    second = owner_client.post(
        "/api/v1/onboarding/complete/", {"privacy_acknowledged": True}, format="json"
    )

    assert second.status_code == 200
    assert second.data["onboarding_completed_at"] == completed_at
    assert ConsentRecord.objects.filter(user=owner, consent_type="wellness_disclaimer").count() == 1
    assert AuditEvent.objects.filter(event_type="onboarding.completed").count() == 1


@pytest.mark.django_db
def test_onboarding_rejects_unknown_fields(owner_client):
    response = owner_client.post(
        "/api/v1/onboarding/complete/",
        {"privacy_acknowledged": True, "skipped": True},
        format="json",
    )

    assert response.status_code == 400
    assert response.data["error"]["code"] == "unknown_field"


@pytest.mark.django_db
def test_onboarding_requires_verified_email(db):
    from rest_framework.test import APIClient

    user = User.objects.create_user(email="unverified@example.com", password="irrelevant")
    client = APIClient()
    client.force_authenticate(user)

    response = client.post(
        "/api/v1/onboarding/complete/", {"privacy_acknowledged": True}, format="json"
    )

    assert response.status_code == 403
    assert response.data["error"]["code"] == "email_not_verified"
