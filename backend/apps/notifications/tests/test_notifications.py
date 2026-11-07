import pytest

from apps.notifications.models import Notification
from apps.notifications.services import notify_security


@pytest.mark.django_db
def test_security_notice_contains_no_private_content(owner):
    notification = notify_security(owner, "password_changed")

    assert notification.category == "security_alert"
    assert notification.link_path.startswith("/")
    assert "password" in notification.body.lower()
    assert owner.email not in notification.body
    assert notification.expires_at is not None


@pytest.mark.django_db
def test_unknown_security_reason_is_a_programming_error(owner):
    with pytest.raises(ValueError):
        notify_security(owner, "not_a_reason")


@pytest.mark.django_db
def test_read_state_constraint(owner):
    from django.db import IntegrityError, transaction

    with pytest.raises(IntegrityError), transaction.atomic():
        Notification.objects.create(
            user=owner,
            category="security_alert",
            title="t",
            body="b",
            is_read=True,
        )
