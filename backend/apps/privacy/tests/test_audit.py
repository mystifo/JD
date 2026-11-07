import pytest
from django.utils import timezone

from common.audit import record
from common.crypto import pseudonym_for


@pytest.mark.django_db
def test_record_writes_event_with_pseudonym(owner):
    event = record(owner, "auth.login", metadata={"method": "password"})

    assert event.pk is not None
    assert event.actor == owner
    assert event.actor_pseudonym == pseudonym_for(owner.pk)
    assert event.metadata == {"method": "password"}
    assert event.created_at <= timezone.now()


@pytest.mark.django_db
def test_record_derives_target_type(owner):
    event = record(owner, "deletion.scheduled", target=owner)
    assert event.target_type == "user"
    assert event.target_id == owner.pk


@pytest.mark.django_db
def test_unknown_event_type_is_rejected(owner):
    with pytest.raises(ValueError):
        record(owner, "auth.not_a_real_event")


@pytest.mark.django_db
def test_metadata_cannot_contain_user_content(owner):
    with pytest.raises(ValueError):
        record(owner, "journal.created", metadata={"content": "private words"})
    with pytest.raises(ValueError):
        record(owner, "journal.created", metadata={"note": "private words"})


@pytest.mark.django_db
def test_audit_rows_are_append_only(owner):
    event = record(owner, "auth.login")
    event.metadata = {"tampered": True}

    with pytest.raises(ValueError):
        event.save()

    with pytest.raises(ValueError):
        event.delete()


@pytest.mark.django_db
def test_actor_can_be_anonymous():
    event = record(None, "auth.login_failed", metadata={"reason": "unknown_email"})
    assert event.actor is None
    assert event.actor_pseudonym is None


@pytest.mark.django_db
def test_target_pair_must_be_complete(owner):
    event = record(owner, "export.requested", target_type="export", target_id=None)
    assert event.target_type is None
    assert event.target_id is None
