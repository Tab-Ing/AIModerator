"""Endpoint de moderación de comentarios."""

from __future__ import annotations

from fastapi import APIRouter

from aimoderator.api.deps import PipelineParam, SessionParam, SettingsParam, TenantParam
from aimoderator.schemas.moderation import ModerationRequest, ModerationResponse
from aimoderator.services.moderation_service import ModerationService

router = APIRouter(tags=["moderación"])


@router.post("/moderate", response_model=ModerationResponse, summary="Moderar un comentario")
async def moderate(
    payload: ModerationRequest,
    tenant: TenantParam,
    session: SessionParam,
    settings: SettingsParam,
    pipeline: PipelineParam,
) -> ModerationResponse:
    """Clasifica un comentario y devuelve la acción de moderación."""
    service = ModerationService(pipeline, settings)
    return await service.moderate(payload, session=session, tenant=tenant)
