"""Tests de integración de uso y cuotas."""

from __future__ import annotations

import asyncio

import helpers
import pytest
from fastapi.testclient import TestClient

from aimoderator.main import create_app

pytestmark = pytest.mark.integration


def _auth(key: str) -> dict[str, str]:
    return {"X-API-Key": key}


def test_usage_reflects_consumption() -> None:
    tenant_id, key = asyncio.run(helpers.seed_tenant(plan="free"))
    try:
        with TestClient(create_app()) as client:
            assert (
                client.post("/v1/moderate", headers=_auth(key), json={"text": "hola"}).status_code
                == 200
            )
            response = client.get("/v1/usage", headers=_auth(key))
            assert response.status_code == 200, response.text
            body = response.json()
            assert body["plan"] == "free"
            assert body["used"] == 1
            assert body["remaining"] == body["quota"] - 1
    finally:
        asyncio.run(helpers.cleanup_tenant(tenant_id))


def test_quota_exceeded_returns_429() -> None:
    tenant_id, key = asyncio.run(helpers.seed_tenant(plan="free"))
    try:
        asyncio.run(helpers.set_daily_usage(tenant_id, 10_000))
        with TestClient(create_app()) as client:
            response = client.post("/v1/moderate", headers=_auth(key), json={"text": "hola"})
            assert response.status_code == 429
            assert response.json()["error"]["code"] == "quota_exceeded"
    finally:
        asyncio.run(helpers.cleanup_tenant(tenant_id))
