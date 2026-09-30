"""Tests de métricas y correlación de solicitudes."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_request_id_header(client: TestClient) -> None:
    response = client.get("/v1/health")
    assert response.headers.get("X-Request-ID")


def test_request_id_is_propagated(client: TestClient) -> None:
    response = client.get("/v1/health", headers={"X-Request-ID": "abc-123"})
    assert response.headers["X-Request-ID"] == "abc-123"


def test_metrics_endpoint(client: TestClient) -> None:
    client.get("/v1/health")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "aimoderator_http_requests_total" in response.text
