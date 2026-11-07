"""Shared abstract models. No domain models live here."""

import uuid

from django.db import models


class UUIDModel(models.Model):
    """Primary key as UUIDv4, generated in the application layer."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class BaseModel(UUIDModel, TimeStampedModel):
    """Convenience base for user-owned rows with both id shapes."""

    class Meta:
        abstract = True


class LocalDateMixin(models.Model):
    """Rows that are unique per user per local calendar day (mood, routines)."""

    local_date = models.DateField()

    class Meta:
        abstract = True
