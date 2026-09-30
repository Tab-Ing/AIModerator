"""Endpoint de moderación de comentarios."""

from __future__ import annotations

from fastapi import APIRouter

from aimoderator.api.deps import (
    HttpClientParam,
    ModerateKeyParam,
    PipelineParam,
    RateLimitParam,
    SessionParam,
    SettingsParam,
)
from aimoderator.db.repositories.profile import get_active_profile
from aimoderator.moderation.pipeline import build_pipeline
from aimoderator.schemas.moderation import ModerationRequest, ModerationResponse
from aimoderator.services.moderation_service import ModerationService
from aimoderator.services.profile_service import ProfileService

router = APIRouter(tags=["moderación"])


@router.post("/moderate", response_model=ModerationResponse, summary="Moderar un comentario")
async def moderate(
    payload: ModerationRequest,
    api_key: ModerateKeyParam,
    _: RateLimitParam,
    session: SessionParam,
    settings: SettingsParam,
    client: HttpClientParam,
    default_pipeline: PipelineParam,
) -> ModerationResponse:
    """Clasifica un comentario según el perfil indicado (o el activo del tenant)."""
    tenant = api_key.tenant

    profile = None
    if payload.profile_id is not None:
        profile = await ProfileService().get(session, tenant.id, payload.profile_id)
    else:
        profile = await get_active_profile(session, tenant.id)

    pipeline = default_pipeline
    if profile is not None:
        pipeline = build_pipeline(
            settings,
            client,
            engine_config=profile.engine_config,
            policy_rules=profile.policy_rules,
        )

    service = ModerationService(pipeline, settings)
    return await service.moderate(payload, session=session, tenant=tenant, profile=profile)
