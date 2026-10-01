"""Router principal de la API v1."""

from __future__ import annotations

from fastapi import APIRouter

from aimoderator.api.v1 import health, jobs, moderate, profiles, usage

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(moderate.router)
api_router.include_router(profiles.router)
api_router.include_router(usage.router)
api_router.include_router(jobs.router)
