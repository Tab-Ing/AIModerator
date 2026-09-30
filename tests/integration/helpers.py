"""Utilidades compartidas por los tests de integración."""

from __future__ import annotations

import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from aimoderator.config import get_settings
from aimoderator.core.security import generate_api_key, hash_api_key
from aimoderator.db.models import ApiKey, ModerationRecord, Profile, Tenant, UsageCounter
from aimoderator.db.repositories.usage import increment_count
from aimoderator.services.usage_service import current_period

_engine = create_async_engine(get_settings().database_url, poolclass=NullPool)
_Session = async_sessionmaker(_engine, expire_on_commit=False)


async def seed_tenant(
    *, plan: str = "free", scopes: list[str] | None = None
) -> tuple[uuid.UUID, str]:
    """Crea un tenant con una API key y devuelve ``(tenant_id, raw_key)``."""
    raw_key = generate_api_key()
    async with _Session() as session:
        tenant = Tenant(name="Integración", slug=f"it-{uuid.uuid4().hex[:8]}", plan=plan)
        session.add(tenant)
        await session.flush()
        session.add(
            ApiKey(
                tenant_id=tenant.id,
                key_hash=hash_api_key(raw_key),
                prefix="aim_",
                scopes=list(scopes or []),
                is_active=True,
            )
        )
        await session.commit()
        return tenant.id, raw_key


async def cleanup_tenant(tenant_id: uuid.UUID) -> None:
    """Borra en orden todos los datos asociados a un tenant."""
    async with _Session() as session:
        await session.execute(
            delete(ModerationRecord).where(ModerationRecord.tenant_id == tenant_id)
        )
        await session.execute(delete(Profile).where(Profile.tenant_id == tenant_id))
        await session.execute(delete(UsageCounter).where(UsageCounter.tenant_id == tenant_id))
        await session.execute(delete(ApiKey).where(ApiKey.tenant_id == tenant_id))
        await session.execute(delete(Tenant).where(Tenant.id == tenant_id))
        await session.commit()


async def count_records(tenant_id: uuid.UUID) -> int:
    async with _Session() as session:
        result = await session.execute(
            select(func.count())
            .select_from(ModerationRecord)
            .where(ModerationRecord.tenant_id == tenant_id)
        )
        return result.scalar_one()


async def latest_record_profile_id(tenant_id: uuid.UUID) -> uuid.UUID | None:
    async with _Session() as session:
        result = await session.execute(
            select(ModerationRecord.profile_id)
            .where(ModerationRecord.tenant_id == tenant_id)
            .order_by(ModerationRecord.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


async def set_daily_usage(tenant_id: uuid.UUID, count: int) -> None:
    """Fija el contador de uso de hoy a ``count``."""
    async with _Session() as session:
        existing = await session.execute(
            select(UsageCounter).where(
                UsageCounter.tenant_id == tenant_id,
                UsageCounter.period == current_period(),
            )
        )
        counter = existing.scalar_one_or_none()
        if counter is None:
            await increment_count(session, tenant_id, current_period(), count)
        else:
            counter.count = count
        await session.commit()
