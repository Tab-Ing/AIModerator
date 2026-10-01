"""Cola de trabajos asíncronos sobre Redis (arq)."""

from __future__ import annotations

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings

from aimoderator.config import Settings


def redis_settings(settings: Settings) -> RedisSettings:
    """Construye la configuración de Redis a partir de la URL."""
    return RedisSettings.from_dsn(settings.redis_url)


async def create_redis_pool(settings: Settings) -> ArqRedis:
    """Crea el pool de conexión a Redis usado por la API y el worker."""
    return await create_pool(redis_settings(settings))
