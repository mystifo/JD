"""Reusable permission classes.

Authorization is always enforced by queryset filtering first; these classes are
defence in depth. Non-owned objects return 404, never 403 (BR-02).
"""

from rest_framework import exceptions
from rest_framework.permissions import BasePermission

NOT_VERIFIED = "Verify your email to use this part of HerSpace."
DELETING = "This account is scheduled for deletion. You can cancel it in Settings."


class IsVerified(BasePermission):
    message = NOT_VERIFIED

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if user.email_verified_at is None:
            raise exceptions.PermissionDenied(detail=NOT_VERIFIED, code="email_not_verified")
        return True


class IsNotDeleting(BasePermission):
    message = DELETING

    def has_permission(self, request, view):
        user = request.user
        # Scheduling a deletion sets is_active=False and refreshes only the
        # requesting session, so an active flag is the single source of truth.
        if not (user and user.is_authenticated and user.is_active):
            raise exceptions.PermissionDenied(detail=DELETING, code="deletion_pending")
        return True


class IsOwner(BasePermission):
    message = "You don't have access to that."

    def has_object_permission(self, request, view, obj):
        owner = (
            getattr(obj, "user", None)
            or getattr(obj, "owner", None)
            or getattr(obj, "requester", None)
        )
        return owner == request.user


class IsStaff(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff)
