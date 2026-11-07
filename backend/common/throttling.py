"""Scoped throttles. Rates live in settings.REST_FRAMEWORK."""

from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class GeneralUserThrottle(UserRateThrottle):
    scope = "user"


class GeneralAnonThrottle(AnonRateThrottle):
    scope = "anon"


class RegisterThrottle(AnonRateThrottle):
    scope = "register"


class LoginThrottle(AnonRateThrottle):
    scope = "login"


class LoginEmailThrottle(AnonRateThrottle):
    """Per-address login limit. Works for anonymous requests by design."""

    scope = "login_email"

    def get_cache_key(self, request, view):
        email = ""
        data = getattr(request, "data", None)
        if isinstance(data, dict):
            email = str(data.get("email", "")).strip().lower()
        if not email:
            return None
        return self.cache_format % {"scope": self.scope, "ident": email}


class PasswordResetThrottle(AnonRateThrottle):
    scope = "password_reset"


class PasswordResetEmailThrottle(AnonRateThrottle):
    scope = "password_reset_email"

    def get_cache_key(self, request, view):
        data = getattr(request, "data", None)
        email = str(data.get("email", "")).strip().lower() if isinstance(data, dict) else ""
        if not email:
            return None
        return self.cache_format % {"scope": self.scope, "ident": email}


class VerifyEmailThrottle(AnonRateThrottle):
    scope = "verify_email"


class PasswordResetConfirmThrottle(AnonRateThrottle):
    scope = "password_reset_confirm"


class VerifyResendThrottle(UserRateThrottle):
    scope = "verify_resend"


class EmailChangeThrottle(UserRateThrottle):
    scope = "email_change"


class InviteThrottle(UserRateThrottle):
    scope = "invite"


class InviteContactThrottle(UserRateThrottle):
    scope = "invite_contact"

    def get_cache_key(self, request, view):
        contact_id = view.kwargs.get("pk") or view.kwargs.get("id")
        if not request.user or not request.user.is_authenticated or not contact_id:
            return None
        return self.cache_format % {
            "scope": self.scope,
            "ident": f"{request.user.pk}:{contact_id}",
        }


class PublicInviteThrottle(AnonRateThrottle):
    scope = "public_invite"


class PublicInviteRespondThrottle(AnonRateThrottle):
    scope = "public_invite_respond"


class PublicSupportThrottle(AnonRateThrottle):
    scope = "public_support"


class PublicSupportRespondThrottle(AnonRateThrottle):
    scope = "public_support_respond"


class ExportRequestThrottle(UserRateThrottle):
    scope = "export_request"


class ExportDownloadThrottle(UserRateThrottle):
    scope = "export_download"


class DeletionThrottle(UserRateThrottle):
    scope = "deletion"
