"""Repositorio de perfiles de uso."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from aimoderator.db.models import Profile


async def list_profiles(session: AsyncSession, tenant_id: uuid.UUID) -> list[Profile]:
    stmt = select(Profile).where(Profile.tenant_id == tenant_id).order_by(Profile.created_at)
    return list((await session.execute(stmt)).scalars().all())


async def get_profile(
    session: AsyncSession, tenant_id: uuid.UUID, profile_id: uuid.UUID
) -> Profile | None:
    stmt = select(Profile).where(Profile.tenant_id == tenant_id, Profile.id == profile_id).limit(1)
    return (await session.execute(stmt)).scalar_one_or_none()


async def get_active_profile(session: AsyncSession, tenant_id: uuid.UUID) -> Profile | None:
    stmt = (
        select(Profile)
        .where(Profile.tenant_id == tenant_id, Profile.is_active.is_(True))
        .order_by(Profile.updated_at.desc())
        .limit(1)
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def create_profile(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    name: str,
    description: str | None,
    engine_config: dict[str, Any],
    policy_rules: dict[str, Any],
) -> Profile:
    profile = Profile(
        tenant_id=tenant_id,
        name=name,
        description=description,
        engine_config=engine_config,
        policy_rules=policy_rules,
    )
    session.add(profile)
    await session.flush()
    return profile


async def deactivate_all(session: AsyncSession, tenant_id: uuid.UUID) -> None:
    await session.execute(
        update(Profile).where(Profile.tenant_id == tenant_id).values(is_active=False)
    )
