"""Authentication services (WF-01 to WF-04).

All state changes happen inside one transaction with their audit event. Email
dispatch is queued with `transaction.on_commit`, and a delivery failure is
logged without PII and never rolled back (workflows.md WF-01).
"""

import logging

from django.conf import settings
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.notifications.services import notify_security
from apps.privacy.services import consent
from apps.profiles.models import UserPreferences, UserProfile
from apps.profiles.services import default_display_name, preferences_for, profile_for
from common.audit import record
from common.exceptions import (
    DeletionPending,
    EmailInUse,
    InvalidCredentials,
    Locked,
    TokenExpired,
    TokenInvalid,
    TokenUsed,
    ValidationFailure,
)
from common.mail import send_template

from ..constants import (
    EMAIL_CHANGE_TTL,
    EMAIL_VERIFICATION_TTL,
    LOCKOUT_DURATION,
    LOCKOUT_THRESHOLD,
    PASSWORD_RESET_TTL,
)
from ..models import EmailChangeRequest, EmailVerificationToken, PasswordResetToken, User
from ..tokens import (
    issue_email_change_request,
    issue_user_token,
    lookup_email_change,
    lookup_token,
)

logger = logging.getLogger(__name__)

# Evaluated once so an unknown address costs the same as a wrong password.
_DUMMY_PASSWORD_HASH = make_password("herspace-timing-equaliser")


def normalize_email(value: str) -> str:
    return (value or "").strip().lower()


def _safe_send(template, *, subject, to, context):
    try:
        send_template(template, subject=subject, to=to, context=context)
    except Exception:  # delivery must never fail the request (WF-01)
        logger.exception("email_send_failed", extra={"template": template})


def _send_verification(user, raw):
    _safe_send(
        "verify_email",
        subject="Verify your HerSpace email",
        to=user.email,
        context={"verify_url": f"{settings.FRONTEND_BASE_URL}/verify-email/{raw}"},
    )


def _send_password_reset(user, raw):
    _safe_send(
        "password_reset",
        subject="Reset your HerSpace password",
        to=user.email,
        context={"reset_url": f"{settings.FRONTEND_BASE_URL}/reset-password/{raw}"},
    )


def _send_email_change_verification(new_email, raw):
    _safe_send(
        "email_change_verify",
        subject="Confirm your new HerSpace email",
        to=new_email,
        context={"verify_url": f"{settings.FRONTEND_BASE_URL}/confirm-email-change/{raw}"},
    )


def _send_email_change_notice(old_email):
    _safe_send(
        "email_change_notice",
        subject="A change to your HerSpace email was requested",
        to=old_email,
        context={},
    )


# --------------------------------------------------------------------------
# Registration and verification
# --------------------------------------------------------------------------


def register_user(
    *,
    email,
    password,
    accept_terms,
    accept_privacy,
    timezone_name,
    display_name,
    request=None,
):
    email = normalize_email(email)
    display_name = (display_name or default_display_name(email)).strip()[:80]

    try:
        with transaction.atomic():
            if User.objects.filter(email__iexact=email).exists():
                raise EmailInUse("That email address is already in use.")
            user = User.objects.create_user(email=email, password=password)
            UserProfile.objects.create(
                user=user,
                display_name=display_name,
                timezone=timezone_name,
            )
            UserPreferences.objects.create(user=user)
            consent.grant(
                user,
                "terms_of_service",
                policy_version=settings.POLICY_TERMS_VERSION,
                request=request,
            )
            consent.grant(
                user,
                "privacy_policy",
                policy_version=settings.POLICY_PRIVACY_VERSION,
                request=request,
            )
            raw, _ = issue_user_token(
                EmailVerificationToken, user, EMAIL_VERIFICATION_TTL, request=request
            )
            record(user, "auth.register", target=user, request=request)
    except IntegrityError as exc:  # unique index race
        raise EmailInUse("That email address is already in use.") from exc

    transaction.on_commit(lambda: _send_verification(user, raw))
    return user


def verify_email(raw, *, request=None):
    token = lookup_token(EmailVerificationToken, raw)
    now = timezone.now()
    with transaction.atomic():
        user = User.objects.select_for_update().get(pk=token.user_id)
        if user.email_verified_at is None:
            user.email_verified_at = now
            user.save(update_fields=["email_verified_at", "updated_at"])
        token.used_at = now
        token.save(update_fields=["used_at"])
        record(user, "auth.email_verified", target=user, request=request)
    return user


def resend_verification(user, *, request=None):
    if user.email_verified_at is not None:
        return False
    with transaction.atomic():
        EmailVerificationToken.objects.filter(user=user, used_at__isnull=True).delete()
        raw, _ = issue_user_token(
            EmailVerificationToken, user, EMAIL_VERIFICATION_TTL, request=request
        )
    transaction.on_commit(lambda: _send_verification(user, raw))
    return True


# --------------------------------------------------------------------------
# Login and sessions
# --------------------------------------------------------------------------


def _locked_error(user, now):
    seconds = max(1, int((user.locked_until - now).total_seconds()))
    return Locked(
        "Too many attempts. Try again in a few minutes.",
        fields={"retry_after_seconds": seconds},
    )


def start_session(email, password, *, request):
    email = normalize_email(email)
    now = timezone.now()
    user = User.objects.filter(email__iexact=email).first()

    if user is not None and user.locked_until is not None:
        if user.locked_until > now:
            raise _locked_error(user, now)
        # The window passed: start a fresh run of attempts.
        user.failed_login_count = 0
        user.locked_until = None
        user.save(update_fields=["failed_login_count", "locked_until", "updated_at"])

    if user is None:
        check_password(password, _DUMMY_PASSWORD_HASH)
        record(None, "auth.login_failed", request=request)
        raise InvalidCredentials("That email and password don't match.")

    if not user.check_password(password):
        _register_failure(user, request=request, now=now)
        raise InvalidCredentials("That email and password don't match.")

    if not user.is_active:
        raise DeletionPending(
            "This account is scheduled for deletion. Use the cancellation link in your email."
        )

    with transaction.atomic():
        user.failed_login_count = 0
        user.locked_until = None
        user.last_login = now
        user.save(update_fields=["failed_login_count", "locked_until", "last_login", "updated_at"])
        django_login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        request.session["auth_session_version"] = user.session_version
        record(user, "auth.login", target=user, request=request)
    return user


def _register_failure(user, *, request, now):
    with transaction.atomic():
        user = User.objects.select_for_update().get(pk=user.pk)
        user.failed_login_count += 1
        locked = False
        if user.failed_login_count >= LOCKOUT_THRESHOLD:
            user.locked_until = now + LOCKOUT_DURATION
            locked = True
        user.save(update_fields=["failed_login_count", "locked_until", "updated_at"])
        record(user, "auth.login_failed", target=user, request=request)
        if locked:
            record(
                user,
                "auth.lockout",
                target=user,
                request=request,
                metadata={"failed_attempts": user.failed_login_count},
            )


def end_session(request):
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        record(user, "auth.logout", target=user, request=request)
        django_logout(request)


def end_all_sessions(request):
    user = request.user
    with transaction.atomic():
        user = User.objects.select_for_update().get(pk=user.pk)
        user.session_version += 1
        user.save(update_fields=["session_version", "updated_at"])
        notify_security(user, "logout_all")
        record(user, "auth.logout_all", target=user, request=request)
    request.session["auth_session_version"] = user.session_version
    return user


# --------------------------------------------------------------------------
# Passwords
# --------------------------------------------------------------------------


def request_password_reset(email, *, request=None):
    user = User.objects.filter(email__iexact=normalize_email(email), is_active=True).first()
    if user is None:
        return None
    with transaction.atomic():
        PasswordResetToken.objects.filter(user=user, used_at__isnull=True).delete()
        raw, _ = issue_user_token(PasswordResetToken, user, PASSWORD_RESET_TTL, request=request)
        record(user, "auth.password_reset_requested", target=user, request=request)
    transaction.on_commit(lambda: _send_password_reset(user, raw))
    return user


def confirm_password_reset(raw, new_password, *, request=None):
    token = lookup_token(PasswordResetToken, raw)
    if token.created_at <= token.user.password_changed_at:
        raise TokenInvalid("This link isn't valid any more. Request a new one.")
    try:
        validate_password(new_password, token.user)
    except DjangoValidationError as exc:
        raise ValidationFailure(
            "Choose a stronger password.",
            fields={"new_password": list(exc.messages)},
        ) from None

    now = timezone.now()
    with transaction.atomic():
        user = User.objects.select_for_update().get(pk=token.user_id)
        user.set_password(new_password)
        user.password_changed_at = now
        user.session_version += 1
        user.save(
            update_fields=[
                "password",
                "password_changed_at",
                "session_version",
                "updated_at",
            ]
        )
        token.used_at = now
        token.save(update_fields=["used_at"])
        PasswordResetToken.objects.filter(user=user).exclude(pk=token.pk).delete()
        notify_security(user, "password_reset")
        record(user, "auth.password_reset_completed", target=user, request=request)
    return user


def change_password(user, current_password, new_password, *, request):
    if not user.check_password(current_password):
        raise ValidationFailure(
            "Your current password isn't right.",
            fields={"current_password": ["Your current password isn't right."]},
        )
    if user.check_password(new_password):
        raise ValidationFailure(
            "Choose a password you haven't used here.",
            fields={"new_password": ["Choose a password you haven't used here."]},
        )

    now = timezone.now()
    with transaction.atomic():
        user = User.objects.select_for_update().get(pk=user.pk)
        user.set_password(new_password)
        user.password_changed_at = now
        user.session_version += 1
        user.save(
            update_fields=[
                "password",
                "password_changed_at",
                "session_version",
                "updated_at",
            ]
        )
        PasswordResetToken.objects.filter(user=user, used_at__isnull=True).delete()
        notify_security(user, "password_changed")
        record(user, "auth.password_changed", target=user, request=request)
    # The current session survives a password change (WF-03): refresh the
    # session auth hash that Django rotates when the password hash changes.
    update_session_auth_hash(request, user)
    request.session["auth_session_version"] = user.session_version
    return user


# --------------------------------------------------------------------------
# Email changes
# --------------------------------------------------------------------------


def request_email_change(user, new_email, current_password, *, request):
    if not user.check_password(current_password):
        raise ValidationFailure(
            "Your current password isn't right.",
            fields={"current_password": ["Your current password isn't right."]},
        )
    new_email = normalize_email(new_email)
    if new_email == user.email:
        raise ValidationFailure(
            "That's already your email address.",
            fields={"new_email": ["That's already your email address."]},
        )
    if User.objects.filter(email__iexact=new_email).exclude(pk=user.pk).exists():
        raise EmailInUse("That email address is already in use.")

    with transaction.atomic():
        EmailChangeRequest.objects.filter(user=user, confirmed_at__isnull=True).delete()
        raw, row = issue_email_change_request(user, new_email, EMAIL_CHANGE_TTL, request=request)
        record(user, "auth.email_change_requested", target=user, request=request)
    old_email = user.email
    transaction.on_commit(lambda: _send_email_change_verification(row.new_email, raw))
    transaction.on_commit(lambda: _send_email_change_notice(old_email))
    return row


def confirm_email_change(raw, *, request=None):
    row = lookup_email_change(raw)
    now = timezone.now()
    try:
        with transaction.atomic():
            row = EmailChangeRequest.objects.select_for_update().get(pk=row.pk)
            if row.confirmed_at is not None:
                raise TokenUsed("This link has already been used.")
            if row.expires_at <= now:
                raise TokenExpired("This link has expired. Request a new one.")
            user = User.objects.select_for_update().get(pk=row.user_id)
            if User.objects.filter(email__iexact=row.new_email).exclude(pk=user.pk).exists():
                raise EmailInUse("That email address is already in use.")
            user.email = normalize_email(row.new_email)
            user.email_verified_at = now
            user.save(update_fields=["email", "email_verified_at", "updated_at"])
            row.confirmed_at = now
            row.save(update_fields=["confirmed_at"])
            record(user, "auth.email_changed", target=user, request=request)
    except IntegrityError as exc:
        raise EmailInUse("That email address is already in use.") from exc
    return user


def session_payload(user):
    profile = profile_for(user)
    preferences = preferences_for(user)
    return {
        "user": {
            "id": user.pk,
            "email": user.email,
            "display_name": profile.display_name,
            "email_verified": user.email_verified_at is not None,
            "timezone": profile.timezone,
        },
        "onboarding_required": profile.onboarding_completed_at is None,
        "deletion_scheduled_for": None,
        "preferences": {
            "theme": preferences.theme,
            "reduced_motion": preferences.reduced_motion,
        },
    }
