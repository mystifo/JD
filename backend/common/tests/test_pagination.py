import pytest
from django.contrib.auth import get_user_model
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from common.exceptions import NotFound, ValidationFailure
from common.pagination import StandardPagination

User = get_user_model()


def _request(**params):
    return Request(APIRequestFactory().get("/api/v1/things/", params))


@pytest.mark.django_db
def test_envelope_shape_and_links(owner):
    for index in range(24):
        User.objects.create_user(email=f"user{index}@example.com", password="x")

    paginator = StandardPagination()
    request = _request(page=2)
    page = paginator.paginate_queryset(User.objects.order_by("email"), request)
    response = paginator.get_paginated_response(list(page))

    body = response.data
    assert body["count"] == 25
    assert body["page"] == 2
    assert body["page_size"] == 20
    assert body["total_pages"] == 2
    assert body["previous"] == "/api/v1/things/?page=1"
    assert body["next"] is None
    assert len(body["results"]) == 5


@pytest.mark.django_db
def test_page_beyond_range_is_404_page_out_of_range(owner):
    paginator = StandardPagination()
    with pytest.raises(NotFound) as excinfo:
        paginator.paginate_queryset(User.objects.all(), _request(page=9), view=None)

    assert excinfo.value.status == 404
    assert excinfo.value.code == "page_out_of_range"


@pytest.mark.django_db
@pytest.mark.parametrize("raw", ["0", "101", "abc", "2.5"])
def test_invalid_page_size_is_rejected(owner, raw):
    paginator = StandardPagination()
    with pytest.raises(ValidationFailure) as excinfo:
        paginator.get_page_size(_request(page_size=raw))

    assert excinfo.value.code == "invalid_page_size"
    assert excinfo.value.status == 400


@pytest.mark.django_db
def test_page_size_is_capped_and_defaulted(owner):
    paginator = StandardPagination()
    assert paginator.get_page_size(_request()) == 20
    assert paginator.get_page_size(_request(page_size="100")) == 100
