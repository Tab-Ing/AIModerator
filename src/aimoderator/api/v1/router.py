"""Router principal de la API v1."""

from __future__ import annotations

from fastapi import APIRouter

from aimoderator.api.v1 import health

api_router = APIRouter()
api_router.include_router(health.router)
