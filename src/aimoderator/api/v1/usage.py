"""Endpoint de uso y cuotas."""

from __future__ import annotations

from fastapi import APIRouter

from aimoderator.api.deps import SessionParam, SettingsParam, UsageReadKeyParam
from aimoderator.schemas.usage import UsageRead
from aimoderator.services.usage_service import UsageService

router = APIRouter(tags=["uso"])


@router.get("/usage", response_model=UsageRead, summary="Consumo y cuota del tenant")
async def get_usage(
    api_key: UsageReadKeyParam, session: SessionParam, settings: SettingsParam
) -> UsageRead:
    return await UsageService(settings).current_usage(session, api_key.tenant)
