"""Repositorio de registros de moderación."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from aimoderator.db.models import ModerationRecord


async def create_moderation_record(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    profile_id: uuid.UUID | None,
    external_id: str | None,
    platform: str | None,
    text_hash: str,
    text_redacted: str | None,
    decision: dict[str, Any],
    engine: str,
    injection_flag: bool,
    latency_ms: int,
) -> ModerationRecord:
    """Persiste una decisión de moderación."""
    record = ModerationRecord(
        tenant_id=tenant_id,
        profile_id=profile_id,
        external_id=external_id,
        platform=platform,
        text_hash=text_hash,
        text_redacted=text_redacted,
        decision=decision,
        engine=engine,
        injection_flag=injection_flag,
        latency_ms=latency_ms,
    )
    session.add(record)
    await session.flush()
    return record


async def list_moderation_records(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    limit: int = 50,
    offset: int = 0,
) -> list[ModerationRecord]:
    stmt = (
        select(ModerationRecord)
        .where(ModerationRecord.tenant_id == tenant_id)
        .order_by(ModerationRecord.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list((await session.execute(stmt)).scalars().all())


async def count_moderation_records(session: AsyncSession, tenant_id: uuid.UUID) -> int:
    stmt = (
        select(func.count())
        .select_from(ModerationRecord)
        .where(ModerationRecord.tenant_id == tenant_id)
    )
    return int((await session.execute(stmt)).scalar_one())
