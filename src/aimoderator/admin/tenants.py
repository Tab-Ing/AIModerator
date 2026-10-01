"""Rutas del panel para tenants, API keys y perfiles."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.exc import IntegrityError

from aimoderator.admin.deps import AdminParam
from aimoderator.admin.templates_env import templates
from aimoderator.api.deps import SessionParam
from aimoderator.config import get_settings
from aimoderator.core.errors import NotFoundError
from aimoderator.core.security import generate_api_key, hash_api_key
from aimoderator.db.models import Tenant
from aimoderator.db.repositories import moderation as moderation_repo
from aimoderator.db.repositories import profile as profile_repo
from aimoderator.db.repositories import tenant as tenant_repo
from aimoderator.schemas.profile import EngineConfig, ProfileCreate
from aimoderator.services.profile_service import ProfileService
from aimoderator.services.usage_service import UsageService

router = APIRouter(tags=["admin-tenants"])


async def _get_tenant(session: SessionParam, tenant_id: uuid.UUID) -> Tenant:
    tenant = await tenant_repo.get_tenant(session, tenant_id)
    if tenant is None:
        raise NotFoundError("Tenant no encontrado")
    return tenant


async def _load_detail(session: SessionParam, tenant: Tenant) -> dict[str, Any]:
    settings = get_settings()
    return {
        "tenant": tenant,
        "api_keys": await tenant_repo.list_api_keys(session, tenant.id),
        "profiles": await profile_repo.list_profiles(session, tenant.id),
        "usage": await UsageService(settings).current_usage(session, tenant),
        "records": await moderation_repo.list_moderation_records(session, tenant.id, limit=10),
        "records_total": await moderation_repo.count_moderation_records(session, tenant.id),
    }


@router.get("/admin/tenants")
async def list_tenants(request: Request, admin: AdminParam, session: SessionParam) -> object:
    tenants = await tenant_repo.list_tenants(session)
    return templates.TemplateResponse(
        request, "tenants.html", {"admin": admin, "tenants": tenants, "error": None}
    )


@router.post("/admin/tenants")
async def create_tenant(
    request: Request,
    admin: AdminParam,
    session: SessionParam,
    name: str = Form(...),
    slug: str = Form(...),
    plan: str = Form("free"),
) -> object:
    try:
        await tenant_repo.create_tenant(session, name=name, slug=slug, plan=plan)
        await session.commit()
    except IntegrityError:
        await session.rollback()
        tenants = await tenant_repo.list_tenants(session)
        return templates.TemplateResponse(
            request,
            "tenants.html",
            {"admin": admin, "tenants": tenants, "error": "El slug ya existe"},
            status_code=409,
        )
    return RedirectResponse("/admin/tenants", status_code=303)


@router.get("/admin/tenants/{tenant_id}")
async def tenant_detail(
    request: Request,
    tenant_id: uuid.UUID,
    admin: AdminParam,
    session: SessionParam,
) -> object:
    tenant = await _get_tenant(session, tenant_id)
    context = await _load_detail(session, tenant)
    context.update({"admin": admin, "new_key": None})
    return templates.TemplateResponse(request, "tenant_detail.html", context)


@router.post("/admin/tenants/{tenant_id}/keys")
async def create_key(
    request: Request,
    tenant_id: uuid.UUID,
    admin: AdminParam,
    session: SessionParam,
    label: str = Form(""),
    scopes: str = Form(""),
) -> object:
    tenant = await _get_tenant(session, tenant_id)
    raw_key = generate_api_key()
    parsed_scopes = [scope.strip() for scope in scopes.split(",") if scope.strip()]
    await tenant_repo.create_api_key(
        session,
        tenant.id,
        key_hash=hash_api_key(raw_key),
        prefix=get_settings().api_key_prefix,
        label=label or None,
        scopes=parsed_scopes,
    )
    await session.commit()
    context = await _load_detail(session, tenant)
    context.update({"admin": admin, "new_key": raw_key})
    return templates.TemplateResponse(request, "tenant_detail.html", context)


@router.post("/admin/tenants/{tenant_id}/keys/{key_id}/revoke")
async def revoke_key(
    tenant_id: uuid.UUID,
    key_id: uuid.UUID,
    admin: AdminParam,
    session: SessionParam,
) -> RedirectResponse:
    api_key = await tenant_repo.get_api_key_by_id(session, key_id)
    if api_key is not None and api_key.tenant_id == tenant_id:
        api_key.is_active = False
        api_key.revoked_at = datetime.now(UTC)
        await session.commit()
    return RedirectResponse(f"/admin/tenants/{tenant_id}", status_code=303)


@router.post("/admin/tenants/{tenant_id}/profiles")
async def create_profile(
    tenant_id: uuid.UUID,
    admin: AdminParam,
    session: SessionParam,
    name: str = Form(...),
    primary: str = Form("heuristic"),
    description: str = Form(""),
    use_pi_guard: str = Form(""),
) -> RedirectResponse:
    await _get_tenant(session, tenant_id)
    payload = ProfileCreate(
        name=name,
        description=description or None,
        engine_config=EngineConfig(primary=primary, use_pi_guard=bool(use_pi_guard)),
    )
    await ProfileService().create(session, tenant_id, payload, actor=f"admin:{admin}")
    return RedirectResponse(f"/admin/tenants/{tenant_id}", status_code=303)


@router.post("/admin/tenants/{tenant_id}/profiles/{profile_id}/activate")
async def activate_profile(
    tenant_id: uuid.UUID,
    profile_id: uuid.UUID,
    admin: AdminParam,
    session: SessionParam,
) -> RedirectResponse:
    await ProfileService().activate(session, tenant_id, profile_id, actor=f"admin:{admin}")
    return RedirectResponse(f"/admin/tenants/{tenant_id}", status_code=303)


@router.post("/admin/tenants/{tenant_id}/profiles/{profile_id}/delete")
async def delete_profile(
    tenant_id: uuid.UUID,
    profile_id: uuid.UUID,
    admin: AdminParam,
    session: SessionParam,
) -> RedirectResponse:
    await ProfileService().delete(session, tenant_id, profile_id, actor=f"admin:{admin}")
    return RedirectResponse(f"/admin/tenants/{tenant_id}", status_code=303)
