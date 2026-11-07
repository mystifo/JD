import pytest

from apps.privacy.models import AuditEvent, ConsentRecord
from apps.profiles.models import UserPreferences
from apps.profiles.services import preferences_for


@pytest.mark.django_db
def test_preferences_defaults(owner_client, owner):
    response = owner_client.get("/api/v1/preferences/")

    assert response.status_code == 200
    assert response.data["theme"] == "system"
    assert response.data["week_starts_on"] == 1
    assert response.data["time_format"] == "24"
    assert response.data["email_notifications_enabled"] is True
    assert response.data["quiet_hours_start"] is None
    assert response.data["calm_default_duration_seconds"] == 300
    assert response.data["dismissed_suggestions"] == []


@pytest.mark.django_db
def test_preferences_update_is_audited_without_values(owner_client, owner):
    response = owner_client.patch(
        "/api/v1/preferences/",
        {
            "theme": "dark",
            "reduced_motion": True,
            "quiet_hours_start": "22:00",
            "quiet_hours_end": "07:00",
        },
        format="json",
    )

    assert response.status_code == 200
    assert response.data["theme"] == "dark"
    assert response.data["reduced_motion"] is True
    assert response.data["quiet_hours_start"] == "22:00"
    assert response.data["quiet_hours_end"] == "07:00"
    event = AuditEvent.objects.get(event_type="preferences.updated")
    assert event.metadata == {
        "changed": ["quiet_hours_end", "quiet_hours_start", "reduced_motion", "theme"]
    }
    assert "dark" not in str(event.metadata)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "payload,field",
    [
        ({"theme": "neon"}, "theme"),
        ({"week_starts_on": 7}, "week_starts_on"),
        ({"week_starts_on": -1}, "week_starts_on"),
        ({"time_format": "36"}, "time_format"),
        ({"calm_default_duration_seconds": 59}, "calm_default_duration_seconds"),
        ({"calm_default_duration_seconds": 3601}, "calm_default_duration_seconds"),
        ({"dismissed_suggestions": ["not_a_real_suggestion"]}, "dismissed_suggestions"),
        ({"dismissed_suggestions": ["try_calm_space", "try_calm_space"]}, "dismissed_suggestions"),
    ],
)
def test_preferences_field_validation(owner_client, payload, field):
    response = owner_client.patch("/api/v1/preferences/", payload, format="json")

    assert response.status_code == 400
    assert field in response.data["error"]["fields"]


@pytest.mark.django_db
def test_quiet_hours_must_be_set_together(owner_client, owner):
    partial = owner_client.patch(
        "/api/v1/preferences/", {"quiet_hours_start": "22:00"}, format="json"
    )
    assert partial.status_code == 400
    assert "quiet_hours_start" in partial.data["error"]["fields"]

    both = owner_client.patch(
        "/api/v1/preferences/",
        {"quiet_hours_start": "22:00", "quiet_hours_end": "07:00"},
        format="json",
    )
    assert both.status_code == 200

    cleared = owner_client.patch(
        "/api/v1/preferences/",
        {"quiet_hours_start": None, "quiet_hours_end": None},
        format="json",
    )
    assert cleared.status_code == 200
    assert cleared.data["quiet_hours_start"] is None


@pytest.mark.django_db
def test_checkin_reminder_requires_a_time(owner_client, owner):
    missing = owner_client.patch(
        "/api/v1/preferences/", {"checkin_reminder_enabled": True}, format="json"
    )
    assert missing.status_code == 400
    assert "checkin_reminder_time" in missing.data["error"]["fields"]

    complete = owner_client.patch(
        "/api/v1/preferences/",
        {"checkin_reminder_enabled": True, "checkin_reminder_time": "09:30"},
        format="json",
    )
    assert complete.status_code == 200
    assert complete.data["checkin_reminder_time"] == "09:30"


@pytest.mark.django_db
def test_email_notification_toggle_writes_consent_history(owner_client, owner):
    off = owner_client.patch(
        "/api/v1/preferences/", {"email_notifications_enabled": False}, format="json"
    )
    assert off.status_code == 200
    revoked = ConsentRecord.objects.get(user=owner, consent_type="email_notifications")
    assert revoked.granted is False
    assert revoked.revoked_at is not None
    assert revoked.granted_at is None

    on = owner_client.patch(
        "/api/v1/preferences/", {"email_notifications_enabled": True}, format="json"
    )
    assert on.status_code == 200
    latest = (
        ConsentRecord.objects.filter(user=owner, consent_type="email_notifications")
        .order_by("-created_at")
        .first()
    )
    assert latest.granted is True
    assert latest.revoked_at is None

    off_again = owner_client.patch(
        "/api/v1/preferences/", {"email_notifications_enabled": False}, format="json"
    )
    assert off_again.status_code == 200
    latest.refresh_from_db()
    assert latest.revoked_at is not None


@pytest.mark.django_db
def test_dismissed_suggestions_round_trip(owner_client, owner):
    response = owner_client.patch(
        "/api/v1/preferences/",
        {"dismissed_suggestions": ["try_calm_space", "add_trusted_contact"]},
        format="json",
    )

    assert response.status_code == 200
    assert response.data["dismissed_suggestions"] == ["try_calm_space", "add_trusted_contact"]
    assert preferences_for(owner).dismissed_suggestions == [
        "try_calm_space",
        "add_trusted_contact",
    ]
    assert UserPreferences.objects.filter(user=owner).count() == 1
