import pytest
from django.utils import timezone

from apps.accounts.models import User
from apps.privacy.models import CONSENT_TYPES, ConsentRecord
from apps.privacy.services import consent


@pytest.mark.django_db
def test_grant_and_revoke_keep_a_latest_state(owner):
    first = consent.grant(owner, "wellness_disclaimer", policy_version="1.0")

    assert consent.is_granted(owner, "wellness_disclaimer") is True
    assert first.granted_at is not None
    assert first.revoked_at is None

    second = consent.grant(owner, "wellness_disclaimer", policy_version="1.0")
    first.refresh_from_db()
    assert first.revoked_at is not None
    assert second.revoked_at is None

    revoked = consent.revoke(owner, "wellness_disclaimer")
    second.refresh_from_db()
    assert second.revoked_at is not None
    assert revoked.granted is False
    assert revoked.revoked_at is not None
    assert consent.is_granted(owner, "wellness_disclaimer") is False


@pytest.mark.django_db
def test_policy_consents_require_a_version(owner):
    with pytest.raises(ValueError):
        consent.grant(owner, "terms_of_service")


@pytest.mark.django_db
def test_unknown_types_and_mismatched_scopes_are_rejected(owner):
    with pytest.raises(ValueError):
        consent.grant(owner, "marketing", policy_version="1.0")
    with pytest.raises(ValueError):
        consent.grant(owner, "support_request_sharing")
    with pytest.raises(ValueError):
        consent.grant(
            owner,
            "support_request_sharing",
            scope_type="contact_invitation",
            scope_id=owner.pk,
        )


@pytest.mark.django_db
def test_scoped_consents_are_separate(owner):
    request_id = owner.pk
    consent.grant(
        owner,
        "support_request_sharing",
        scope_type="support_request",
        scope_id=request_id,
    )

    assert consent.is_granted(
        owner, "support_request_sharing", scope_type="support_request", scope_id=request_id
    )
    other_id = User.objects.create_user(email="x@example.com", password="irrelevant").pk
    assert not consent.is_granted(
        owner,
        "support_request_sharing",
        scope_type="support_request",
        scope_id=other_id,
    )


@pytest.mark.django_db
def test_consent_rows_capture_request_evidence(owner, rf):
    request = rf.post("/api/v1/onboarding/complete/")
    request.META["REMOTE_ADDR"] = "203.0.113.9"
    request.META["HTTP_USER_AGENT"] = "Mozilla/5.0 Chrome/131.0.0.0"

    row = consent.grant(owner, "email_notifications", request=request)

    assert row.ip_hash is not None
    assert row.user_agent_family == "Chrome/131.0.0.0"
    assert row.ip_hash != "203.0.113.9"


@pytest.mark.django_db
def test_consent_type_vocabulary_is_closed(owner):
    from django.db import IntegrityError, transaction

    with pytest.raises(IntegrityError), transaction.atomic():
        ConsentRecord.objects.create(
            user=owner,
            consent_type="not_a_consent",
            granted=True,
            granted_at=timezone.now(),
        )

    assert "wellness_disclaimer" in CONSENT_TYPES
