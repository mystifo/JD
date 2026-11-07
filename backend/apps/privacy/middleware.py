"""Per-request correlation id and audit context."""

import uuid

from common.logging_filters import request_id_var


class RequestContextMiddleware:
    """Attach a validated request id to the request, logs, and response."""

    header = "X-Request-ID"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.request_id = self._request_id(request)
        token = request_id_var.set(str(request.request_id))
        try:
            response = self.get_response(request)
        finally:
            request_id_var.reset(token)
        response[self.header] = str(request.request_id)
        return response

    def _request_id(self, request):
        raw = request.headers.get(self.header)
        if raw:
            try:
                return uuid.UUID(raw)
            except (TypeError, ValueError):
                pass
        return uuid.uuid4()
