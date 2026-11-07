import uuid

import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_health_reports_database_status():
    response = APIClient().get("/api/v1/health/")

    assert response.status_code == 200
    assert response.data["status"] == "ok"
    assert response.data["database"] == "ok"
    assert response.data["version"]
    assert response.data["time"].endswith("Z")
    assert response["Cache-Control"] == "no-store"


@pytest.mark.django_db
def test_health_is_public():
    response = APIClient().get("/api/v1/health/")
    assert response.status_code != 401


@pytest.mark.django_db
def test_request_id_is_generated_and_returned():
    response = APIClient().get("/api/v1/health/")

    raw = response["X-Request-ID"]
    assert uuid.UUID(raw)


@pytest.mark.django_db
def test_client_request_id_is_echoed_when_valid():
    request_id = str(uuid.uuid4())
    response = APIClient().get("/api/v1/health/", HTTP_X_REQUEST_ID=request_id)

    assert response["X-Request-ID"] == request_id


@pytest.mark.django_db
def test_invalid_client_request_id_is_replaced():
    response = APIClient().get("/api/v1/health/", HTTP_X_REQUEST_ID="not-a-uuid")

    assert response["X-Request-ID"] != "not-a-uuid"
    assert uuid.UUID(response["X-Request-ID"])


@pytest.mark.django_db
def test_health_returns_503_without_internals_when_database_fails(monkeypatch):
    def boom():
        raise RuntimeError("connection refused at 10.0.0.5:5432")

    monkeypatch.setattr("config.health.connection.ensure_connection", boom)
    response = APIClient().get("/api/v1/health/")

    assert response.status_code == 503
    assert response.data == {
        "status": "degraded",
        "database": "error",
        "version": response.data["version"],
        "time": response.data["time"],
    }
    assert "10.0.0.5" not in response.content.decode()
