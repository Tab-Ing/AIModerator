"""Dependencias de FastAPI compartidas."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from aimoderator.config import Settings, get_settings
from aimoderator.core.errors import UnauthorizedError
from aimoderator.core.security import hash_api_key
from aimoderator.db.models import Tenant
from aimoderator.db.repositories.tenant import get_api_key
from aimoderator.db.session import get_session
from aimoderator.moderation.pipeline import ModerationPipeline


def settings_dep() -> Settings:
    """Inyecta la configuración de la aplicación."""
    return get_settings()


async def session_dep() -> AsyncIterator[AsyncSession]:
    """Inyecta una sesión de base de datos."""
    async for session in get_session():
        yield session


SettingsDep = Depends(settings_dep)
SessionDep = Depends(session_dep)

SessionParam = Annotated[AsyncSession, Depends(session_dep)]
SettingsParam = Annotated[Settings, Depends(settings_dep)]


async def get_current_tenant(
    session: SessionParam,
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> Tenant:
    """Resuelve el tenant a partir de la API key del encabezado ``X-API-Key``."""
    if not x_api_key:
        raise UnauthorizedError("Falta el encabezado X-API-Key")

    api_key = await get_api_key(session, hash_api_key(x_api_key))
    if api_key is None:
        raise UnauthorizedError("API key inválida o revocada")

    api_key.last_used_at = datetime.now(UTC)
    await session.commit()
    return api_key.tenant


TenantParam = Annotated[Tenant, Depends(get_current_tenant)]


def get_pipeline(request: Request) -> ModerationPipeline:
    """Recupera el pipeline de moderación inicializado en el lifespan."""
    pipeline = getattr(request.app.state, "pipeline", None)
    if not isinstance(pipeline, ModerationPipeline):
        raise RuntimeError("El pipeline de moderación no está inicializado")
    return pipeline


PipelineParam = Annotated[ModerationPipeline, Depends(get_pipeline)]
