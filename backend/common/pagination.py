"""Standard pagination envelope (api-documentation.md §1.4)."""

import math

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .exceptions import NotFound, ValidationFailure


class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
    invalid_page_message = "page_out_of_range"

    def get_page_size(self, request):
        raw = request.query_params.get(self.page_size_query_param)
        if raw is None:
            return self.page_size
        try:
            size = int(raw)
        except (TypeError, ValueError):
            raise ValidationFailure(
                "page_size must be a whole number.",
                code="invalid_page_size",
                fields={"page_size": ["Enter a whole number between 1 and 100."]},
            ) from None
        if size < 1 or size > self.max_page_size:
            raise ValidationFailure(
                "page_size must be between 1 and 100.",
                code="invalid_page_size",
                fields={"page_size": ["Enter a whole number between 1 and 100."]},
            )
        return size

    def paginate_queryset(self, queryset, request, view=None):
        page_number = request.query_params.get(self.page_query_param, 1)
        paginator = self.django_paginator_class(queryset, self.get_page_size(request))
        try:
            page_number = int(page_number)
        except (TypeError, ValueError):
            raise NotFound("That page doesn't exist.", code="page_out_of_range") from None
        if page_number < 1 or page_number > paginator.num_pages:
            raise NotFound("That page doesn't exist.", code="page_out_of_range")
        self.request = request
        self.page = paginator.page(page_number)
        return list(self.page)

    def get_paginated_response(self, data):
        page_size = self.page.paginator.per_page
        count = self.page.paginator.count
        total_pages = max(1, math.ceil(count / page_size)) if count else 1
        next_link = self._link(True, self.page.next_page_number()) if self.page.has_next() else None
        previous_link = (
            self._link(True, self.page.previous_page_number()) if self.page.has_previous() else None
        )
        return Response(
            {
                "count": count,
                "page": self.page.number,
                "page_size": page_size,
                "total_pages": total_pages,
                "next": next_link,
                "previous": previous_link,
                "results": data,
            }
        )

    def _link(self, present, page_number):
        if not present:
            return None
        params = self.request.query_params.copy()
        params["page"] = page_number
        return f"{self.request.path}?{params.urlencode()}"
