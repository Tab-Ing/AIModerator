"""Dependencias de FastAPI compartidas."""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from aimoderator.config import Settings, get_settings
from aimoderator.db.session import get_session


def settings_dep() -> Settings:
    """Inyecta la configuración de la aplicación."""
    return get_settings()


async def session_dep() -> AsyncIterator[AsyncSession]:
    """Inyecta una sesión de base de datos."""
    async for session in get_session():
        yield session


SettingsDep = Depends(settings_dep)
SessionDep = Depends(session_dep)
