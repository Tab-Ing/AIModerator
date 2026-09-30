"""Tests de integración de perfiles de uso y scopes."""

from __future__ import annotations

import asyncio
import uuid

import helpers
import pytest
from fastapi.testclient import TestClient

from aimoderator.main import create_app

pytestmark = pytest.mark.integration


def _auth(key: str) -> dict[str, str]:
    return {"X-API-Key": key}


def test_profiles_crud_and_activation() -> None:
    tenant_id, key = asyncio.run(helpers.seed_tenant())
    try:
        with TestClient(create_app()) as client:
            response = client.post("/v1/profiles", headers=_auth(key), json={"name": "estricto"})
            assert response.status_code == 201, response.text
            profile = response.json()
            profile_id = profile["id"]
            assert profile["version"] == 1
            assert profile["is_active"] is False
            assert profile["engine_config"]["primary"] == "heuristic"

            listing = client.get("/v1/profiles", headers=_auth(key))
            assert listing.status_code == 200
            assert len(listing.json()) == 1

            fetched = client.get(f"/v1/profiles/{profile_id}", headers=_auth(key))
            assert fetched.status_code == 200

            updated = client.patch(
                f"/v1/profiles/{profile_id}",
                headers=_auth(key),
                json={"policy_rules": {"default_action": "flag"}},
            )
            assert updated.status_code == 200
            assert updated.json()["version"] == 2
            assert updated.json()["policy_rules"]["default_action"] == "flag"

            activated = client.post(f"/v1/profiles/{profile_id}/activate", headers=_auth(key))
            assert activated.status_code == 200
            assert activated.json()["is_active"] is True

            deleted = client.delete(f"/v1/profiles/{profile_id}", headers=_auth(key))
            assert deleted.status_code == 204
            assert client.get("/v1/profiles", headers=_auth(key)).json() == []
    finally:
        asyncio.run(helpers.cleanup_tenant(tenant_id))


def test_profile_is_scoped_to_tenant() -> None:
    tenant_a, key_a = asyncio.run(helpers.seed_tenant())
    tenant_b, key_b = asyncio.run(helpers.seed_tenant())
    try:
        with TestClient(create_app()) as client:
            created = client.post("/v1/profiles", headers=_auth(key_a), json={"name": "a"}).json()
            response = client.get(f"/v1/profiles/{created['id']}", headers=_auth(key_b))
            assert response.status_code == 404
    finally:
        asyncio.run(helpers.cleanup_tenant(tenant_a))
        asyncio.run(helpers.cleanup_tenant(tenant_b))


def test_scopes_are_enforced() -> None:
    tenant_id, key = asyncio.run(helpers.seed_tenant(scopes=["profiles:read"]))
    try:
        with TestClient(create_app()) as client:
            assert client.get("/v1/profiles", headers=_auth(key)).status_code == 200
            assert (
                client.post("/v1/profiles", headers=_auth(key), json={"name": "x"}).status_code
                == 403
            )
            assert (
                client.post("/v1/moderate", headers=_auth(key), json={"text": "hola"}).status_code
                == 403
            )
    finally:
        asyncio.run(helpers.cleanup_tenant(tenant_id))


def test_moderate_uses_active_profile() -> None:
    tenant_id, key = asyncio.run(helpers.seed_tenant())
    try:
        with TestClient(create_app()) as client:
            created = client.post("/v1/profiles", headers=_auth(key), json={"name": "p1"}).json()
            profile_id = uuid.UUID(created["id"])

            explicit = client.post(
                "/v1/moderate",
                headers=_auth(key),
                json={"text": "Hola mundo", "profile_id": created["id"]},
            )
            assert explicit.status_code == 200, explicit.text
            assert explicit.json()["action"] == "allow"
            assert asyncio.run(helpers.latest_record_profile_id(tenant_id)) == profile_id

            assert (
                client.post(f"/v1/profiles/{profile_id}/activate", headers=_auth(key)).status_code
                == 200
            )
            fallback = client.post("/v1/moderate", headers=_auth(key), json={"text": "otro"})
            assert fallback.status_code == 200
    finally:
        asyncio.run(helpers.cleanup_tenant(tenant_id))
