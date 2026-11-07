"""Authentication endpoints (api-documentation.md §4)."""

from django.middleware.csrf import get_token
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from common.crypto import mask_email
from common.permissions import IsNotDeleting, IsVerified
from common.throttling import (
    EmailChangeThrottle,
    LoginEmailThrottle,
    LoginThrottle,
    PasswordResetConfirmThrottle,
    PasswordResetEmailThrottle,
    PasswordResetThrottle,
    RegisterThrottle,
    VerifyEmailThrottle,
    VerifyResendThrottle,
)
from common.views import CsrfProtectedAPIView

from . import services
from .serializers import (
    EmailChangedSerializer,
    EmailChangeResponseSerializer,
    EmailChangeSerializer,
    EmailVerifiedSerializer,
    LoginSerializer,
    PasswordChangedSerializer,
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestResponseSerializer,
    PasswordResetRequestSerializer,
    RegisterResponseSerializer,
    RegisterSerializer,
    SentSerializer,
    SessionSerializer,
    TokenSerializer,
)

ERROR = {"400": OpenApiResponse(description="Validation failure"), "429": OpenApiResponse()}


class RegisterView(CsrfProtectedAPIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [RegisterThrottle]

    @extend_schema(
        request=RegisterSerializer,
        responses={201: RegisterResponseSerializer, **ERROR, 409: OpenApiResponse()},
        tags=["auth"],
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = services.register_user(
            email=data["email"],
            password=data["password"],
            accept_terms=data["accept_terms"],
            accept_privacy=data["accept_privacy"],
            timezone_name=data["timezone"],
            display_name=data.get("display_name"),
            request=request,
        )
        return Response(
            {
                "id": user.pk,
                "email": user.email,
                "email_verified": False,
                "onboarding_required": True,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(CsrfProtectedAPIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle, LoginEmailThrottle]

    @extend_schema(
        request=LoginSerializer,
        responses={
            200: SessionSerializer,
            401: OpenApiResponse(description="Invalid credentials"),
            403: OpenApiResponse(description="Deletion pending"),
            423: OpenApiResponse(description="Account locked"),
            429: OpenApiResponse(description="Rate limited"),
        },
        tags=["auth"],
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = services.start_session(
            serializer.validated_data["email"],
            serializer.validated_data["password"],
            request=request,
        )
        return Response(services.session_payload(user))


class LogoutView(CsrfProtectedAPIView):
    permission_classes = [AllowAny]

    @extend_schema(request=None, responses={204: OpenApiResponse()}, tags=["auth"])
    def post(self, request):
        services.end_session(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class LogoutAllView(CsrfProtectedAPIView):
    permission_classes = [IsAuthenticated, IsVerified, IsNotDeleting]

    @extend_schema(request=None, responses={204: OpenApiResponse()}, tags=["auth"])
    def post(self, request):
        services.end_all_sessions(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SessionView(CsrfProtectedAPIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: SessionSerializer}, tags=["auth"])
    def get(self, request):
        return Response(services.session_payload(request.user))


class CsrfView(CsrfProtectedAPIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(request=None, responses={204: OpenApiResponse()}, tags=["auth"])
    def get(self, request):
        get_token(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class VerifyEmailView(CsrfProtectedAPIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [VerifyEmailThrottle]

    @extend_schema(
        request=TokenSerializer,
        responses={200: EmailVerifiedSerializer, 409: OpenApiResponse(), 410: OpenApiResponse()},
        tags=["auth"],
    )
    def post(self, request):
        serializer = TokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.verify_email(serializer.validated_data["token"], request=request)
        return Response({"email_verified": True})


class VerifyEmailResendView(CsrfProtectedAPIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [VerifyResendThrottle]

    @extend_schema(
        request=None, responses={200: SentSerializer, 202: SentSerializer}, tags=["auth"]
    )
    def post(self, request):
        sent = services.resend_verification(request.user, request=request)
        if not sent:
            return Response({"sent": False}, status=status.HTTP_200_OK)
        return Response({"sent": True}, status=status.HTTP_202_ACCEPTED)


class PasswordResetView(CsrfProtectedAPIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [PasswordResetThrottle, PasswordResetEmailThrottle]
    message = "If that address has an account, a reset link is on its way."

    @extend_schema(
        request=PasswordResetRequestSerializer,
        responses={202: PasswordResetRequestResponseSerializer, 429: OpenApiResponse()},
        tags=["auth"],
    )
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.request_password_reset(serializer.validated_data["email"], request=request)
        return Response({"message": self.message}, status=status.HTTP_202_ACCEPTED)


class PasswordResetConfirmView(CsrfProtectedAPIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [PasswordResetConfirmThrottle]

    @extend_schema(
        request=PasswordResetConfirmSerializer,
        responses={
            200: PasswordChangedSerializer,
            400: OpenApiResponse(),
            409: OpenApiResponse(),
            410: OpenApiResponse(),
        },
        tags=["auth"],
    )
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.confirm_password_reset(
            serializer.validated_data["token"],
            serializer.validated_data["new_password"],
            request=request,
        )
        return Response({"password_changed": True})


class PasswordChangeView(CsrfProtectedAPIView):
    permission_classes = [IsAuthenticated, IsVerified, IsNotDeleting]

    @extend_schema(
        request=PasswordChangeSerializer,
        responses={200: PasswordChangedSerializer, 400: OpenApiResponse()},
        tags=["auth"],
    )
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={"user": request.user})
        serializer.is_valid(raise_exception=True)
        services.change_password(
            request.user,
            serializer.validated_data["current_password"],
            serializer.validated_data["new_password"],
            request=request,
        )
        return Response({"password_changed": True})


class EmailChangeView(CsrfProtectedAPIView):
    permission_classes = [IsAuthenticated, IsVerified, IsNotDeleting]
    throttle_classes = [EmailChangeThrottle]

    @extend_schema(
        request=EmailChangeSerializer,
        responses={
            202: EmailChangeResponseSerializer,
            400: OpenApiResponse(),
            409: OpenApiResponse(),
        },
        tags=["auth"],
    )
    def post(self, request):
        serializer = EmailChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        row = services.request_email_change(
            request.user,
            serializer.validated_data["new_email"],
            serializer.validated_data["current_password"],
            request=request,
        )
        return Response(
            {"pending": True, "new_email": mask_email(row.new_email)},
            status=status.HTTP_202_ACCEPTED,
        )


class EmailChangeConfirmView(CsrfProtectedAPIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        request=TokenSerializer,
        responses={
            200: EmailChangedSerializer,
            409: OpenApiResponse(),
            410: OpenApiResponse(),
        },
        tags=["auth"],
    )
    def post(self, request):
        serializer = TokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = services.confirm_email_change(serializer.validated_data["token"], request=request)
        return Response({"email": user.email, "email_verified": True})
