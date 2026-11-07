"""Profile and preference access helpers."""

from django.db import transaction
from django.utils import timezone

from .models import UserPreferences, UserProfile


def default_display_name(email: str) -> str:
    local = (email or "").split("@", 1)[0]
    words = local.replace(".", " ").replace("_", " ").replace("-", " ").strip()
    name = " ".join(word.capitalize() for word in words.split())
    return (name or "Friend")[:80]


def profile_for(user):
    profile, _ = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            "display_name": default_display_name(user.email),
            "timezone": "UTC",
        },
    )
    return profile


def preferences_for(user):
    preferences, _ = UserPreferences.objects.get_or_create(user=user)
    return preferences


def complete_onboarding(user, *, policy_version, request=None):
    """Set the completion timestamp once and record the wellness consent."""
    from apps.privacy.services import consent

    with transaction.atomic():
        profile = UserProfile.objects.select_for_update().get_or_create(
            user=user,
            defaults={
                "display_name": default_display_name(user.email),
                "timezone": "UTC",
            },
        )[0]
        if profile.onboarding_completed_at is not None:
            return profile
        profile.onboarding_completed_at = timezone.now()
        profile.save(update_fields=["onboarding_completed_at", "updated_at"])
        consent.grant(
            user,
            "wellness_disclaimer",
            policy_version=policy_version,
            request=request,
        )
        return profile


def onboarding_required(user) -> bool:
    return profile_for(user).onboarding_completed_at is None


def touch_profile(user, changes):
    profile = profile_for(user)
    for field, value in changes.items():
        setattr(profile, field, value)
    profile.save()
    return profile


def touch_preferences(user, changes):
    preferences = preferences_for(user)
    for field, value in changes.items():
        setattr(preferences, field, value)
    preferences.save()
    return preferences


def active_email_notifications_consent(user):
    from apps.privacy.models import ConsentRecord

    return (
        ConsentRecord.objects.filter(
            user=user,
            consent_type="email_notifications",
            scope_type__isnull=True,
            scope_id__isnull=True,
            granted=True,
            revoked_at__isnull=True,
        )
        .order_by("-created_at")
        .first()
    )
