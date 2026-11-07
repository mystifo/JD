"""Authentication routes. Mounted under `/api/v1`."""

from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("auth/register/", views.RegisterView.as_view(), name="register"),
    path("auth/login/", views.LoginView.as_view(), name="login"),
    path("auth/logout/", views.LogoutView.as_view(), name="logout"),
    path("auth/logout-all/", views.LogoutAllView.as_view(), name="logout-all"),
    path("auth/session/", views.SessionView.as_view(), name="session"),
    path("auth/csrf/", views.CsrfView.as_view(), name="csrf"),
    path("auth/verify-email/", views.VerifyEmailView.as_view(), name="verify-email"),
    path(
        "auth/verify-email/resend/",
        views.VerifyEmailResendView.as_view(),
        name="verify-email-resend",
    ),
    path("auth/password-reset/", views.PasswordResetView.as_view(), name="password-reset"),
    path(
        "auth/password-reset/confirm/",
        views.PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
    path("auth/password-change/", views.PasswordChangeView.as_view(), name="password-change"),
    path("auth/email-change/", views.EmailChangeView.as_view(), name="email-change"),
    path(
        "auth/email-change/confirm/",
        views.EmailChangeConfirmView.as_view(),
        name="email-change-confirm",
    ),
]
