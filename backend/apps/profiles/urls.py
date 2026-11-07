"""Profile and preference routes. Mounted under `/api/v1`."""

from django.urls import path

from . import views

app_name = "profiles"

urlpatterns = [
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("preferences/", views.PreferencesView.as_view(), name="preferences"),
    path(
        "onboarding/complete/",
        views.OnboardingCompleteView.as_view(),
        name="onboarding-complete",
    ),
]
