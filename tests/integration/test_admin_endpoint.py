"""Tests de integración del panel de administración."""

from __future__ import annotations

import asyncio
import uuid

import helpers
import pytest
from fastapi.testclient import TestClient

from aimoderator.main import create_app

pytestmark = pytest.mark.integration


def test_admin_requires_login() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/admin", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/admin/login"


def test_admin_login_and_manage_tenant() -> None:
    tenant_id, _key = asyncio.run(helpers.seed_tenant())
    slug = f"admin-{uuid.uuid4().hex[:8]}"
    try:
        with TestClient(create_app()) as client:
            bad = client.post(
                "/admin/login",
                data={"username": "admin", "password": "wrong"},
                follow_redirects=False,
            )
            assert bad.status_code == 401

            good = client.post(
                "/admin/login",
                data={"username": "admin", "password": "admin"},
                follow_redirects=False,
            )
            assert good.status_code == 303
            assert client.get("/admin").status_code == 200
            assert client.get("/admin/tenants").status_code == 200
            assert client.get("/admin/partials/status").status_code == 200

            created = client.post(
                "/admin/tenants",
                data={"name": "Nueva", "slug": slug, "plan": "free"},
                follow_redirects=False,
            )
            assert created.status_code == 303

            detail = client.get(f"/admin/tenants/{tenant_id}")
            assert detail.status_code == 200
            assert "API keys" in detail.text

            new_key = client.post(
                f"/admin/tenants/{tenant_id}/keys",
                data={"label": "ci", "scopes": "moderate"},
            )
            assert new_key.status_code == 200
            assert "Nueva API key" in new_key.text

            profile = client.post(
                f"/admin/tenants/{tenant_id}/profiles",
                data={"name": "estricto", "primary": "heuristic", "use_pi_guard": "on"},
                follow_redirects=False,
            )
            assert profile.status_code == 303
            assert "estricto" in client.get(f"/admin/tenants/{tenant_id}").text
    finally:
        asyncio.run(helpers.cleanup_tenant(tenant_id))
        asyncio.run(helpers.delete_tenant_by_slug(slug))
