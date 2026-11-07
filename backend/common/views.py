"""API view base classes."""

from django.middleware.csrf import CsrfViewMiddleware
from rest_framework import exceptions
from rest_framework.views import APIView

SAFE_METHODS = ("GET", "HEAD", "OPTIONS", "TRACE")


class CsrfProtectedAPIView(APIView):
    """Enforce CSRF on unsafe methods even for anonymous requests.

    DRF's `SessionAuthentication` only checks CSRF once a session exists, so a
    login or registration POST would otherwise be unprotected. Public token
    endpoints that the contract exempts set `csrf_protected = False`.

    The check runs in `initial()` so a failure is raised inside `dispatch()`
    and rendered by DRF's exception handler as the standard error envelope.
    """

    csrf_protected = True

    def initial(self, request, *args, **kwargs):
        if self.csrf_protected and request.method not in SAFE_METHODS:
            check = CsrfViewMiddleware(lambda current: None)
            if check.process_view(request, None, (), {}) is not None:
                raise exceptions.PermissionDenied(
                    "Your session expired. Refresh the page and try again."
                )
        super().initial(request, *args, **kwargs)
