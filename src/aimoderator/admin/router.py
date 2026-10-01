"""Router agregado del panel de administración."""

from __future__ import annotations

from fastapi import APIRouter

from aimoderator.admin import auth, dashboard, tenants

router = APIRouter()
router.include_router(auth.router)
router.include_router(dashboard.router)
router.include_router(tenants.router)
