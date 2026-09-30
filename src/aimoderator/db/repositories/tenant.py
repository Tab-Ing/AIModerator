"""Repositorio de tenants y API keys."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from aimoderator.db.models import ApiKey


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
