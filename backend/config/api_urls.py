"""`/api/v1` router composition.

Each app contributes a URL module; empty modules are intentional at M1 and are
filled in by later milestones without changing this file's shape.
"""

from django.urls import include, path

from config.health import HealthView

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("", include("apps.accounts.urls")),
    path("", include("apps.profiles.urls")),
    path("", include("apps.wellness.urls")),
    path("", include("apps.connections.urls")),
    path("", include("apps.journal.urls")),
    path("", include("apps.selfcare.urls")),
    path("", include("apps.calm_space.urls")),
    path("", include("apps.insights.urls")),
    path("", include("apps.notifications.urls")),
    path("", include("apps.privacy.urls")),
]
