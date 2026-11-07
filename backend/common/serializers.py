"""Serializer base classes shared by the API."""

from rest_framework import serializers

from common.exceptions import UnknownField


class StrictFieldsMixin:
    """Reject unknown body fields (api-documentation.md §1.1).

    DRF silently ignores extra keys by default, which hides client bugs and
    makes typo'd consent flags look accepted. The API contract is a 400 with
    code `unknown_field`.
    """

    def to_internal_value(self, data):
        if isinstance(data, dict):
            unknown = sorted(set(data) - set(self.fields))
            if unknown:
                raise UnknownField(
                    "Some fields aren't recognised.",
                    fields={key: ["Unknown field."] for key in unknown},
                )
        return super().to_internal_value(data)


class StrictSerializer(StrictFieldsMixin, serializers.Serializer):
    pass


class StrictModelSerializer(StrictFieldsMixin, serializers.ModelSerializer):
    pass
