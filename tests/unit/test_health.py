"""Tests de los endpoints de sistema."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    response = client.get("/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_version(client: TestClient) -> None:
    response = client.get("/v1/version")
    assert response.status_code == 200
    assert response.json()["name"] == "aimoderator"


def test_root(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["docs"] == "/docs"
