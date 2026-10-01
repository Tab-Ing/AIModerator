"""Repositorio de tenants y API keys."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from aimoderator.db.models import ApiKey, Tenant


async def get_api_key(session: AsyncSession, key_hash: str) -> ApiKey | None:
    """Busca una API key activa (y no revocada) por su hash, con su tenant."""
    stmt = (
        select(ApiKey)
        .where(
            ApiKey.key_hash == key_hash,
            ApiKey.is_active.is_(True),
            ApiKey.revoked_at.is_(None),
        )
        .options(selectinload(ApiKey.tenant))
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def list_tenants(session: AsyncSession) -> list[Tenant]:
    stmt = select(Tenant).order_by(Tenant.created_at.desc())
    return list((await session.execute(stmt)).scalars().all())


async def get_tenant(session: AsyncSession, tenant_id: uuid.UUID) -> Tenant | None:
    return await session.get(Tenant, tenant_id)


async def create_tenant(
    session: AsyncSession, *, name: str, slug: str, plan: str = "free"
) -> Tenant:
    tenant = Tenant(name=name, slug=slug, plan=plan)
    session.add(tenant)
    await session.flush()
    return tenant


async def list_api_keys(session: AsyncSession, tenant_id: uuid.UUID) -> list[ApiKey]:
    stmt = select(ApiKey).where(ApiKey.tenant_id == tenant_id).order_by(ApiKey.created_at.desc())
    return list((await session.execute(stmt)).scalars().all())


async def create_api_key(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    key_hash: str,
    prefix: str,
    label: str | None,
    scopes: list[str],
) -> ApiKey:
    api_key = ApiKey(
        tenant_id=tenant_id,
        key_hash=key_hash,
        prefix=prefix,
        label=label,
        scopes=scopes,
        is_active=True,
    )
    session.add(api_key)
    await session.flush()
    return api_key


async def get_api_key_by_id(session: AsyncSession, api_key_id: uuid.UUID) -> ApiKey | None:
    return await session.get(ApiKey, api_key_id)
