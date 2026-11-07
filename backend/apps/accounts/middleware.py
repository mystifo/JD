"""Session-version enforcement.

`session_version` is stamped into the session on login. Bumping the user row
(password change/reset, logout-all, deactivation) makes every other session
fail on its next request (security.md §4).
"""

from django.contrib.auth import logout as django_logout
from django.contrib.auth.models import AnonymousUser


class SessionVersionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            stored = request.session.get("auth_session_version")
            if stored is not None and stored != user.session_version:
                django_logout(request)
                request.user = AnonymousUser()
        return self.get_response(request)
