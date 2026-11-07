"""Profile and preference serializers."""

from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import serializers

from common.exceptions import ValidationFailure
from common.serializers import StrictModelSerializer, StrictSerializer
from common.validators import validate_timezone

from .models import DISMISSIBLE_SUGGESTIONS, UserPreferences, UserProfile


class ProfileSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="user_id", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    email_verified = serializers.SerializerMethodField()
    display_name = serializers.CharField()
    pronouns = serializers.CharField(allow_null=True)
    bio = serializers.CharField(allow_null=True)
    timezone = serializers.CharField()
    locale = serializers.CharField()

    class Meta:
        model = UserProfile
        fields = (
            "id",
            "display_name",
            "pronouns",
            "bio",
            "date_of_birth",
            "timezone",
            "locale",
            "email",
            "email_verified",
            "onboarding_completed_at",
            "created_at",
        )

    def get_email_verified(self, obj) -> bool:
        return obj.user.email_verified_at is not None


class ProfileUpdateSerializer(StrictModelSerializer):
    display_name = serializers.CharField(max_length=80, allow_blank=False)
    pronouns = serializers.CharField(
        max_length=40, allow_null=True, allow_blank=True, required=False
    )
    bio = serializers.CharField(max_length=280, allow_null=True, allow_blank=True, required=False)
    date_of_birth = serializers.DateField(allow_null=True, required=False)
    timezone = serializers.CharField(max_length=64, required=False)
    locale = serializers.ChoiceField(choices=("en",), required=False)

    class Meta:
        model = UserProfile
        fields = ("display_name", "pronouns", "bio", "date_of_birth", "timezone", "locale")

    def validate_timezone(self, value):
        try:
            validate_timezone(value)
        except DjangoValidationError as exc:
            raise ValidationFailure(
                "Enter a valid time zone.",
                code="invalid_timezone",
                fields={"timezone": list(exc.messages)},
            ) from None
        return value

    def validate_date_of_birth(self, value):
        if value is None:
            return value
        today = timezone.localdate()
        if value >= today:
            raise serializers.ValidationError("Date of birth must be in the past.")
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        if age < 13:
            raise serializers.ValidationError("You must be at least 13 years old to use HerSpace.")
        return value


class PreferencesSerializer(StrictModelSerializer):
    theme = serializers.ChoiceField(choices=("system", "light", "dark"))
    week_starts_on = serializers.IntegerField(min_value=0, max_value=6)
    time_format = serializers.ChoiceField(choices=("12", "24"))
    date_format = serializers.CharField(max_length=20)
    checkin_reminder_time = serializers.TimeField(allow_null=True, required=False, format="%H:%M")
    quiet_hours_start = serializers.TimeField(allow_null=True, required=False, format="%H:%M")
    quiet_hours_end = serializers.TimeField(allow_null=True, required=False, format="%H:%M")
    calm_default_duration_seconds = serializers.IntegerField(min_value=60, max_value=3600)
    dismissed_suggestions = serializers.ListField(
        child=serializers.ChoiceField(choices=DISMISSIBLE_SUGGESTIONS),
        required=False,
    )

    class Meta:
        model = UserPreferences
        fields = (
            "theme",
            "reduced_motion",
            "week_starts_on",
            "time_format",
            "date_format",
            "checkin_reminder_enabled",
            "checkin_reminder_time",
            "routine_reminders_enabled",
            "hydration_reminders_enabled",
            "in_app_notifications_enabled",
            "email_notifications_enabled",
            "support_notifications_enabled",
            "quiet_hours_start",
            "quiet_hours_end",
            "calm_default_duration_seconds",
            "calm_sound_enabled",
            "dismissed_suggestions",
        )

    def validate_dismissed_suggestions(self, value):
        if len(set(value)) != len(value):
            raise serializers.ValidationError("Each suggestion can only appear once.")
        return value

    def validate(self, attrs):
        instance = self.instance
        start = attrs.get("quiet_hours_start", getattr(instance, "quiet_hours_start", None))
        end = attrs.get("quiet_hours_end", getattr(instance, "quiet_hours_end", None))
        if (start is None) != (end is None):
            raise serializers.ValidationError(
                {"quiet_hours_start": ["Set both quiet hours or neither."]}
            )

        enabled = attrs.get(
            "checkin_reminder_enabled",
            getattr(instance, "checkin_reminder_enabled", False),
        )
        reminder_time = attrs.get(
            "checkin_reminder_time",
            getattr(instance, "checkin_reminder_time", None),
        )
        if enabled and reminder_time is None:
            raise serializers.ValidationError(
                {"checkin_reminder_time": ["Choose a time for your check-in reminder."]}
            )
        return attrs


class OnboardingCompleteSerializer(StrictSerializer):
    privacy_acknowledged = serializers.BooleanField()


class OnboardingCompleteResponseSerializer(serializers.Serializer):
    onboarding_completed_at = serializers.DateTimeField()
