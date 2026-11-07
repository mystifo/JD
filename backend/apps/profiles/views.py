"""Profile, preferences, and onboarding endpoints (api-documentation.md §5)."""

from django.conf import settings
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.privacy.services import consent
from common.audit import record
from common.exceptions import ConsentRequired
from common.permissions import IsNotDeleting, IsVerified
from common.views import CsrfProtectedAPIView

from .serializers import (
    OnboardingCompleteResponseSerializer,
    OnboardingCompleteSerializer,
    PreferencesSerializer,
    ProfileSerializer,
    ProfileUpdateSerializer,
)
from .services import complete_onboarding, preferences_for, profile_for


class ProfileView(CsrfProtectedAPIView):
    permission_classes = [IsAuthenticated, IsVerified, IsNotDeleting]

    @extend_schema(responses={200: ProfileSerializer}, tags=["profile"])
    def get(self, request):
        return Response(ProfileSerializer(profile_for(request.user)).data)

    @extend_schema(
        request=ProfileUpdateSerializer,
        responses={200: ProfileSerializer, 400: OpenApiResponse()},
        tags=["profile"],
    )
    def patch(self, request):
        profile = profile_for(request.user)
        serializer = ProfileUpdateSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        changed = sorted(serializer.validated_data)
        profile = serializer.save()
        if changed:
            record(
                request.user,
                "profile.updated",
                target=request.user,
                request=request,
                metadata={"changed": changed},
            )
        return Response(ProfileSerializer(profile).data)


class PreferencesView(CsrfProtectedAPIView):
    permission_classes = [IsAuthenticated, IsVerified, IsNotDeleting]

    @extend_schema(responses={200: PreferencesSerializer}, tags=["profile"])
    def get(self, request):
        return Response(PreferencesSerializer(preferences_for(request.user)).data)

    @extend_schema(
        request=PreferencesSerializer,
        responses={200: PreferencesSerializer, 400: OpenApiResponse()},
        tags=["profile"],
    )
    def patch(self, request):
        preferences = preferences_for(request.user)
        serializer = PreferencesSerializer(preferences, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        changed = sorted(serializer.validated_data)
        preferences = serializer.save()
        if "email_notifications_enabled" in changed:
            consent.set_email_notifications(
                request.user,
                preferences.email_notifications_enabled,
                request=request,
            )
        if changed:
            record(
                request.user,
                "preferences.updated",
                target=request.user,
                request=request,
                metadata={"changed": changed},
            )
        return Response(PreferencesSerializer(preferences).data)


class OnboardingCompleteView(CsrfProtectedAPIView):
    permission_classes = [IsAuthenticated, IsVerified, IsNotDeleting]

    @extend_schema(
        request=OnboardingCompleteSerializer,
        responses={200: OnboardingCompleteResponseSerializer, 400: OpenApiResponse()},
        tags=["profile"],
    )
    def post(self, request):
        serializer = OnboardingCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not serializer.validated_data["privacy_acknowledged"]:
            raise ConsentRequired("Acknowledge the privacy explanation to finish onboarding.")

        profile = profile_for(request.user)
        already_complete = profile.onboarding_completed_at is not None
        profile = complete_onboarding(
            request.user,
            policy_version=settings.POLICY_WELLNESS_VERSION,
            request=request,
        )
        if not already_complete:
            record(request.user, "onboarding.completed", target=request.user, request=request)
        return Response(
            {"onboarding_completed_at": profile.onboarding_completed_at},
            status=status.HTTP_200_OK,
        )
