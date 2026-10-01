"""Dashboard del panel: métricas y estado de la cola."""

from __future__ import annotations

from typing import Any

from arq.constants import default_queue_name, in_progress_key_prefix
from fastapi import APIRouter, Request

from aimoderator.admin.deps import AdminParam
from aimoderator.admin.templates_env import templates
from aimoderator.config import Settings, get_settings
from aimoderator.core import metrics

router = APIRouter(tags=["admin-dashboard"])


async def _queue_status(request: Request, settings: Settings) -> dict[str, Any]:
    redis = getattr(request.app.state, "redis", None)
    if redis is None:
        return {"enabled": False, "reachable": False, "pending": 0, "in_progress": 0}
    try:
        await redis.ping()
        pending = int(await redis.zcard(default_queue_name))
        in_progress = len(await redis.keys(f"{in_progress_key_prefix}*"))
    except Exception:  # noqa: BLE001
        return {"enabled": True, "reachable": False, "pending": 0, "in_progress": 0}
    return {"enabled": True, "reachable": True, "pending": pending, "in_progress": in_progress}


@router.get("/admin")
async def dashboard(request: Request, admin: AdminParam) -> object:
    settings = get_settings()
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "admin": admin,
            "stats": metrics.snapshot(),
            "queue": await _queue_status(request, settings),
            "env": settings.env,
        },
    )


@router.get("/admin/partials/status")
async def status_partial(request: Request, admin: AdminParam) -> object:
    settings = get_settings()
    return templates.TemplateResponse(
        request,
        "partials/status.html",
        {
            "stats": metrics.snapshot(),
            "queue": await _queue_status(request, settings),
        },
    )
