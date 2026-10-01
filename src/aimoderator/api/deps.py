"""Dependencias de FastAPI compartidas."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Annotated

import httpx
from arq.connections import ArqRedis
from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from aimoderator.config import Settings, get_settings
from aimoderator.core.errors import (
    ForbiddenError,
    QueueUnavailableError,
    RateLimitError,
    UnauthorizedError,
)
from aimoderator.core.rate_limit import get_rate_limiter
from aimoderator.core.security import hash_api_key
from aimoderator.db.models import ApiKey, Tenant
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


SessionParam = Annotated[AsyncSession, Depends(session_dep)]
SettingsParam = Annotated[Settings, Depends(settings_dep)]


async def get_current_api_key(
    session: SessionParam,
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> ApiKey:
    """Resuelve la API key del encabezado ``X-API-Key`` con su tenant."""
    if not x_api_key:
        raise UnauthorizedError("Falta el encabezado X-API-Key")

    api_key = await get_api_key(session, hash_api_key(x_api_key))
    if api_key is None:
        raise UnauthorizedError("API key inválida o revocada")

    api_key.last_used_at = datetime.now(UTC)
    await session.commit()
    return api_key


ApiKeyParam = Annotated[ApiKey, Depends(get_current_api_key)]


async def get_current_tenant(api_key: ApiKeyParam) -> Tenant:
    """Devuelve el tenant asociado a la API key autenticada."""
    return api_key.tenant


TenantParam = Annotated[Tenant, Depends(get_current_tenant)]


def _require_scopes(api_key: ApiKey, required: set[str]) -> None:
    granted = set(api_key.scopes or [])
    if granted and not (granted & required):
        raise ForbiddenError("La API key no tiene el scope requerido")


async def scope_moderate(api_key: ApiKeyParam) -> ApiKey:
    _require_scopes(api_key, {"moderate"})
    return api_key


async def scope_profiles_read(api_key: ApiKeyParam) -> ApiKey:
    _require_scopes(api_key, {"profiles:read", "profiles:write"})
    return api_key


async def scope_profiles_write(api_key: ApiKeyParam) -> ApiKey:
    _require_scopes(api_key, {"profiles:write"})
    return api_key


async def scope_usage_read(api_key: ApiKeyParam) -> ApiKey:
    _require_scopes(api_key, {"usage:read"})
    return api_key


ModerateKeyParam = Annotated[ApiKey, Depends(scope_moderate)]
ProfilesReadKeyParam = Annotated[ApiKey, Depends(scope_profiles_read)]
ProfilesWriteKeyParam = Annotated[ApiKey, Depends(scope_profiles_write)]
UsageReadKeyParam = Annotated[ApiKey, Depends(scope_usage_read)]


async def enforce_rate_limit(api_key: ApiKeyParam, settings: SettingsParam) -> None:
    """Aplica el límite de solicitudes por minuto de la API key."""
    limiter = get_rate_limiter(settings.rate_limit_per_minute)
    if not limiter.allow(str(api_key.id)):
        raise RateLimitError("Demasiadas solicitudes; intentá más tarde")


RateLimitParam = Annotated[None, Depends(enforce_rate_limit)]


def get_http_client(request: Request) -> httpx.AsyncClient:
    """Recupera el cliente HTTP compartido inicializado en el lifespan."""
    client = getattr(request.app.state, "http_client", None)
    if not isinstance(client, httpx.AsyncClient):
        raise RuntimeError("El cliente HTTP no está inicializado")
    return client


HttpClientParam = Annotated[httpx.AsyncClient, Depends(get_http_client)]


def get_pipeline(request: Request) -> ModerationPipeline:
    """Recupera el pipeline de moderación inicializado en el lifespan."""
    pipeline = getattr(request.app.state, "pipeline", None)
    if not isinstance(pipeline, ModerationPipeline):
        raise RuntimeError("El pipeline de moderación no está inicializado")
    return pipeline


PipelineParam = Annotated[ModerationPipeline, Depends(get_pipeline)]


def get_redis(request: Request) -> ArqRedis:
    """Recupera el pool de Redis de la cola (si está habilitada)."""
    redis = getattr(request.app.state, "redis", None)
    if not isinstance(redis, ArqRedis):
        raise QueueUnavailableError("La cola de trabajos no está habilitada")
    return redis


RedisParam = Annotated[ArqRedis, Depends(get_redis)]
