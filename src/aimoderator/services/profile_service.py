"""Servicio de perfiles de uso (CRUD, versionado y activación)."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from aimoderator.core.errors import NotFoundError
from aimoderator.db.models import Profile
from aimoderator.db.repositories import profile as profile_repo
from aimoderator.db.repositories.audit import create_audit_log
from aimoderator.schemas.profile import ProfileCreate, ProfileUpdate


class ProfileService:
    """Opera perfiles siempre acotados al tenant."""

    async def list(self, session: AsyncSession, tenant_id: uuid.UUID) -> list[Profile]:
        return await profile_repo.list_profiles(session, tenant_id)

    async def get(
        self, session: AsyncSession, tenant_id: uuid.UUID, profile_id: uuid.UUID
    ) -> Profile:
        profile = await profile_repo.get_profile(session, tenant_id, profile_id)
        if profile is None:
            raise NotFoundError("Perfil no encontrado")
        return profile

    async def create(
        self,
        session: AsyncSession,
        tenant_id: uuid.UUID,
        data: ProfileCreate,
        *,
        actor: str | None = None,
    ) -> Profile:
        profile = await profile_repo.create_profile(
            session,
            tenant_id,
            name=data.name,
            description=data.description,
            engine_config=data.engine_config.model_dump(mode="json"),
            policy_rules=data.policy_rules.model_dump(mode="json"),
        )
        await create_audit_log(
            session,
            tenant_id=tenant_id,
            actor=actor,
            action="profile.create",
            payload={"profile_id": str(profile.id), "name": profile.name},
        )
        await session.commit()
        await session.refresh(profile)
        return profile

    async def update(
        self,
        session: AsyncSession,
        tenant_id: uuid.UUID,
        profile_id: uuid.UUID,
        data: ProfileUpdate,
        *,
        actor: str | None = None,
    ) -> Profile:
        profile = await self.get(session, tenant_id, profile_id)
        if data.name is not None:
            profile.name = data.name
        if data.description is not None:
            profile.description = data.description
        if data.engine_config is not None:
            profile.engine_config = data.engine_config.model_dump(mode="json")
        if data.policy_rules is not None:
            profile.policy_rules = data.policy_rules.model_dump(mode="json")
        profile.version += 1
        await create_audit_log(
            session,
            tenant_id=tenant_id,
            actor=actor,
            action="profile.update",
            payload={"profile_id": str(profile.id), "version": profile.version},
        )
        await session.commit()
        await session.refresh(profile)
        return profile

    async def delete(
        self,
        session: AsyncSession,
        tenant_id: uuid.UUID,
        profile_id: uuid.UUID,
        *,
        actor: str | None = None,
    ) -> None:
        profile = await self.get(session, tenant_id, profile_id)
        await create_audit_log(
            session,
            tenant_id=tenant_id,
            actor=actor,
            action="profile.delete",
            payload={"profile_id": str(profile.id), "name": profile.name},
        )
        await session.delete(profile)
        await session.commit()

    async def activate(
        self,
        session: AsyncSession,
        tenant_id: uuid.UUID,
        profile_id: uuid.UUID,
        *,
        actor: str | None = None,
    ) -> Profile:
        profile = await self.get(session, tenant_id, profile_id)
        await profile_repo.deactivate_all(session, tenant_id)
        profile.is_active = True
        await create_audit_log(
            session,
            tenant_id=tenant_id,
            actor=actor,
            action="profile.activate",
            payload={"profile_id": str(profile.id), "name": profile.name},
        )
        await session.commit()
        await session.refresh(profile)
        return profile
