"""Repositorio de contadores de uso (cuotas por período)."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from aimoderator.db.models import UsageCounter


async def get_count(session: AsyncSession, tenant_id: uuid.UUID, period: str) -> int:
    stmt = select(UsageCounter.count).where(
        UsageCounter.tenant_id == tenant_id, UsageCounter.period == period
    )
    value = (await session.execute(stmt)).scalar_one_or_none()
    return int(value or 0)


async def increment_count(
    session: AsyncSession, tenant_id: uuid.UUID, period: str, amount: int = 1
) -> int:
    stmt = (
        pg_insert(UsageCounter)
        .values(tenant_id=tenant_id, period=period, count=amount)
        .on_conflict_do_update(
            index_elements=["tenant_id", "period"],
            set_={"count": UsageCounter.__table__.c.count + amount},
        )
        .returning(UsageCounter.count)
    )
    return int((await session.execute(stmt)).scalar_one())
