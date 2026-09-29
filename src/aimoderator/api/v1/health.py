"""Endpoints de estado del sistema."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from sqlalchemy import text

from aimoderator import __version__
from aimoderator.db.session import SessionLocal

router = APIRouter(tags=["sistema"])


@router.get("/health", summary="Liveness")
async def health() -> dict[str, str]:
    """Indica que el proceso está vivo."""
    return {"status": "ok", "version": __version__}


@router.get("/ready", summary="Readiness")
async def ready() -> dict[str, str]:
    """Comprueba conectividad con PostgreSQL."""
    async with SessionLocal() as session:
        await session.execute(text("SELECT 1"))
    return {"status": "ready"}


@router.get("/version", summary="Versión")
async def version() -> dict[str, Any]:
    """Devuelve el nombre y la versión del servicio."""
    return {"name": "aimoderator", "version": __version__}
