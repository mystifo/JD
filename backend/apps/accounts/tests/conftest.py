"""Shared auth test helpers."""

import pytest
from django.core.cache import cache

from apps.accounts.models import User

PASSWORD = "correct-horse-battery-staple"
NEW_PASSWORD = "a-different-long-password-42"


@pytest.fixture(autouse=True)
def clear_throttle_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def registered(anon_client, django_capture_on_commit_callbacks):
    payload = {
        "email": "mira@example.com",
        "password": PASSWORD,
        "accept_terms": True,
        "accept_privacy": True,
        "timezone": "Europe/Berlin",
        "display_name": "Mira",
    }
    with django_capture_on_commit_callbacks(execute=True):
        response = anon_client.post("/api/v1/auth/register/", payload, format="json")
    assert response.status_code == 201, response.data
    return User.objects.get(email="mira@example.com")


@pytest.fixture
def verified_user(db):
    from django.utils import timezone

    return User.objects.create_user(
        email="verified@example.com",
        password=PASSWORD,
        email_verified_at=timezone.now(),
    )
