"""Shared fixtures: two users, their clients, and an anonymous client."""

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User

PASSWORD = "correct-horse-battery-staple"


@pytest.fixture
def owner(db):
    return User.objects.create_user(
        email="owner@example.com",
        password=PASSWORD,
        email_verified_at=timezone.now(),
    )


@pytest.fixture
def other_user(db):
    return User.objects.create_user(
        email="other@example.com",
        password=PASSWORD,
        email_verified_at=timezone.now(),
    )


@pytest.fixture
def owner_client(owner):
    client = APIClient()
    client.force_authenticate(owner)
    return client


@pytest.fixture
def other_client(other_user):
    client = APIClient()
    client.force_authenticate(other_user)
    return client


@pytest.fixture
def anon_client():
    return APIClient()
