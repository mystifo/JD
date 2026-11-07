import pytest
from django.db import IntegrityError, transaction

from apps.accounts.models import User

PASSWORD = "correct-horse-battery-staple"


@pytest.mark.django_db
def test_create_user_normalises_email():
    user = User.objects.create_user(email="Mira@Example.COM", password=PASSWORD)

    assert user.email == "mira@example.com"
    assert user.check_password(PASSWORD)
    assert user.is_active
    assert not user.is_staff
    assert str(user) == f"User({user.pk})"
    assert "mira" not in str(user)


@pytest.mark.django_db
def test_email_is_case_insensitive_when_looking_up():
    User.objects.create_user(email="mira@example.com", password=PASSWORD)

    assert User.objects.filter(email__iexact="MIRA@EXAMPLE.COM").exists()


@pytest.mark.django_db
def test_email_uniqueness_is_case_insensitive():
    User.objects.create_user(email="mira@example.com", password=PASSWORD)

    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.create(email="Mira@Example.com", password="hashed")


@pytest.mark.django_db
def test_create_superuser_sets_flags():
    admin = User.objects.create_superuser(email="admin@example.com", password=PASSWORD)

    assert admin.is_staff
    assert admin.is_superuser
    assert admin.is_active


@pytest.mark.django_db
def test_create_user_requires_email():
    with pytest.raises(ValueError):
        User.objects.create_user(email="", password=PASSWORD)


@pytest.mark.django_db
def test_primary_key_is_a_uuid():
    user = User.objects.create_user(email="mira@example.com", password=PASSWORD)
    assert user.pk.int is not None
    assert user.pk.version == 4
