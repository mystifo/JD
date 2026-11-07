"""Profile and preference models (database-design.md §4)."""

from django.conf import settings
from django.db import models

from common.models import TimeStampedModel, UUIDModel
from common.validators import validate_timezone

THEMES = ("system", "light", "dark")
TIME_FORMATS = ("12", "24")
LOCALES = ("en",)

# Closed vocabulary of dismissible dashboard suggestions (FR-PROF-06).
DISMISSIBLE_SUGGESTIONS = (
    "add_trusted_contact",
    "first_mood_checkin",
    "set_checkin_reminder",
    "write_first_journal_entry",
    "try_calm_space",
    "create_routine",
)


class UserProfile(UUIDModel, TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    display_name = models.CharField(max_length=80)
    pronouns = models.CharField(  # noqa: DJ001 - nullable by schema
        max_length=40, null=True, blank=True
    )
    bio = models.CharField(max_length=280, null=True, blank=True)  # noqa: DJ001 - nullable
    date_of_birth = models.DateField(null=True, blank=True)
    timezone = models.CharField(max_length=64, default="UTC", validators=[validate_timezone])
    locale = models.CharField(max_length=10, default="en")
    onboarding_completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "profiles_userprofile"
        ordering = ["-created_at"]
        # Length checks are added with RunSQL in migration 0001: Django has no
        # portable `char_length` lookup, and PostgreSQL's regex engine rejects
        # the `[\s\S]` idiom with "invalid repetition count(s)".

    def __str__(self):
        # Display names are user content; never emit them in logs/admin.
        return f"UserProfile({self.user_id})"


class UserPreferences(UUIDModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="preferences",
    )
    theme = models.CharField(max_length=10, default="system", choices=[(t, t) for t in THEMES])
    reduced_motion = models.BooleanField(default=False)
    week_starts_on = models.PositiveSmallIntegerField(default=1)
    time_format = models.CharField(
        max_length=2, default="24", choices=[(t, t) for t in TIME_FORMATS]
    )
    date_format = models.CharField(max_length=20, default="d MMM yyyy")
    checkin_reminder_enabled = models.BooleanField(default=False)
    checkin_reminder_time = models.TimeField(null=True, blank=True)
    routine_reminders_enabled = models.BooleanField(default=False)
    hydration_reminders_enabled = models.BooleanField(default=False)
    in_app_notifications_enabled = models.BooleanField(default=True)
    email_notifications_enabled = models.BooleanField(default=True)
    support_notifications_enabled = models.BooleanField(default=True)
    quiet_hours_start = models.TimeField(null=True, blank=True)
    quiet_hours_end = models.TimeField(null=True, blank=True)
    calm_default_duration_seconds = models.PositiveSmallIntegerField(default=300)
    calm_sound_enabled = models.BooleanField(default=False)
    dismissed_suggestions = models.JSONField(default=list)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "profiles_userpreferences"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(theme__in=THEMES), name="chk_userpreferences_theme"
            ),
            models.CheckConstraint(
                condition=models.Q(week_starts_on__range=(0, 6)),
                name="chk_userpreferences_week_start",
            ),
            models.CheckConstraint(
                condition=models.Q(time_format__in=TIME_FORMATS),
                name="chk_userpreferences_time_format",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(quiet_hours_start__isnull=True)
                    & models.Q(quiet_hours_end__isnull=True)
                )
                | (
                    models.Q(quiet_hours_start__isnull=False)
                    & models.Q(quiet_hours_end__isnull=False)
                ),
                name="chk_userpreferences_quiet_hours_pair",
            ),
            models.CheckConstraint(
                condition=models.Q(calm_default_duration_seconds__range=(60, 3600)),
                name="chk_userpreferences_calm_duration",
            ),
        ]

    def __str__(self):
        return f"UserPreferences({self.user_id})"
