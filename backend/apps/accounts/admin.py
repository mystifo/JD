"""Admin for the user model only. User content is never registered."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("-date_joined",)
    list_display = ("id", "email", "is_active", "is_staff", "email_verified_at", "date_joined")
    list_filter = ("is_active", "is_staff", "is_superuser")
    search_fields = ("email",)
    readonly_fields = (
        "id",
        "email",
        "password",
        "last_login",
        "date_joined",
        "email_verified_at",
        "password_changed_at",
        "session_version",
        "failed_login_count",
        "locked_until",
    )
    fieldsets = (
        (None, {"fields": ("id", "email", "password")}),
        ("Flags", {"fields": ("is_active", "is_staff", "is_superuser")}),
        ("Security", {"fields": ("email_verified_at", "password_changed_at", "session_version")}),
        ("Lockout", {"fields": ("failed_login_count", "locked_until")}),
        ("Dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "is_staff", "is_superuser"),
            },
        ),
    )

    def has_delete_permission(self, request, obj=None):
        return False
