"""Liveness/readiness probe used by the load balancer and Compose."""

from django.conf import settings
from django.db import connection
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthSerializer(serializers.Serializer):
    status = serializers.CharField()
    database = serializers.CharField()
    version = serializers.CharField(required=False)
    time = serializers.DateTimeField(required=False)


class HealthView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = []

    @extend_schema(responses={200: HealthSerializer, 503: HealthSerializer}, tags=["system"])
    def get(self, request):
        try:
            connection.ensure_connection()
            database = "ok"
        except Exception:  # pragma: no cover - only on infrastructure failure
            database = "error"

        healthy = database == "ok"
        payload = {
            "status": "ok" if healthy else "degraded",
            "database": database,
            "version": settings.APP_VERSION,
            "time": timezone.now().isoformat().replace("+00:00", "Z"),
        }
        response = Response(
            payload,
            status=status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
        )
        response["Cache-Control"] = "no-store"
        return response
