"""Authentication request/response serializers."""

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from common.serializers import StrictSerializer
from common.validators import validate_timezone

from .models import User


def password_errors(password, *, user=None):
    try:
        validate_password(password, user)
    except DjangoValidationError as exc:
        return list(exc.messages)
    return []


class RegisterSerializer(StrictSerializer):
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(trim_whitespace=False, write_only=True)
    accept_terms = serializers.BooleanField()
    accept_privacy = serializers.BooleanField()
    timezone = serializers.CharField(max_length=64, required=False, default="UTC")
    display_name = serializers.CharField(max_length=80, required=False, allow_blank=False)

    def validate_email(self, value):
        return value.strip().lower()

    def validate_timezone(self, value):
        try:
            validate_timezone(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from None
        return value

    def validate(self, attrs):
        if not attrs.get("accept_terms") or not attrs.get("accept_privacy"):
            raise serializers.ValidationError(
                {"consents": ["Accept the Terms of Service and Privacy Policy to continue."]}
            )
        errors = password_errors(attrs["password"], user=User(email=attrs["email"]))
        if errors:
            raise serializers.ValidationError({"password": errors})
        return attrs


class RegisterResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    email = serializers.EmailField()
    email_verified = serializers.BooleanField()
    onboarding_required = serializers.BooleanField()


class LoginSerializer(StrictSerializer):
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(trim_whitespace=False, write_only=True)

    def validate_email(self, value):
        return value.strip().lower()


class TokenSerializer(StrictSerializer):
    token = serializers.CharField(trim_whitespace=True)


class PasswordResetRequestSerializer(StrictSerializer):
    email = serializers.EmailField(max_length=254)

    def validate_email(self, value):
        return value.strip().lower()


class PasswordResetRequestResponseSerializer(serializers.Serializer):
    message = serializers.CharField()


class PasswordResetConfirmSerializer(StrictSerializer):
    token = serializers.CharField(trim_whitespace=True)
    new_password = serializers.CharField(trim_whitespace=False, write_only=True)


class PasswordChangeSerializer(StrictSerializer):
    current_password = serializers.CharField(trim_whitespace=False, write_only=True)
    new_password = serializers.CharField(trim_whitespace=False, write_only=True)

    def validate_new_password(self, value):
        errors = password_errors(value, user=self.context.get("user"))
        if errors:
            raise serializers.ValidationError(errors)
        return value


class EmailChangeSerializer(StrictSerializer):
    new_email = serializers.EmailField(max_length=254)
    current_password = serializers.CharField(trim_whitespace=False, write_only=True)

    def validate_new_email(self, value):
        return value.strip().lower()


class EmailChangeResponseSerializer(serializers.Serializer):
    pending = serializers.BooleanField()
    new_email = serializers.CharField()


class PasswordChangedSerializer(serializers.Serializer):
    password_changed = serializers.BooleanField()


class EmailVerifiedSerializer(serializers.Serializer):
    email_verified = serializers.BooleanField()


class EmailChangedSerializer(serializers.Serializer):
    email = serializers.EmailField()
    email_verified = serializers.BooleanField()


class SentSerializer(serializers.Serializer):
    sent = serializers.BooleanField()


class SessionUserSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    email = serializers.EmailField()
    display_name = serializers.CharField()
    email_verified = serializers.BooleanField()
    timezone = serializers.CharField()


class SessionPreferencesSerializer(serializers.Serializer):
    theme = serializers.CharField()
    reduced_motion = serializers.BooleanField()


class SessionSerializer(serializers.Serializer):
    user = SessionUserSerializer()
    onboarding_required = serializers.BooleanField()
    deletion_scheduled_for = serializers.DateTimeField(allow_null=True)
    preferences = SessionPreferencesSerializer()
