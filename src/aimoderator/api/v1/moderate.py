"""Endpoints de moderación de comentarios."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter

from aimoderator.api.deps import (
    HttpClientParam,
    ModerateKeyParam,
    PipelineParam,
    RateLimitParam,
    SessionParam,
    SettingsParam,
)
from aimoderator.db.models import Profile, Tenant
from aimoderator.db.repositories.profile import get_active_profile
from aimoderator.moderation.pipeline import ModerationPipeline, build_pipeline
from aimoderator.schemas.moderation import (
    BatchModerationRequest,
    BatchModerationResponse,
    ModerationRequest,
    ModerationResponse,
)
from aimoderator.services.moderation_service import ModerationService
from aimoderator.services.profile_service import ProfileService

router = APIRouter(tags=["moderación"])


async def _resolve_profile(
    session: SessionParam, tenant: Tenant, profile_id: UUID | None
) -> Profile | None:
    if profile_id is not None:
        return await ProfileService().get(session, tenant.id, profile_id)
    return await get_active_profile(session, tenant.id)


def _pipeline_for(
    profile: Profile | None,
    settings: SettingsParam,
    client: HttpClientParam,
    default_pipeline: ModerationPipeline,
) -> ModerationPipeline:
    if profile is None:
        return default_pipeline
    return build_pipeline(
        settings,
        client,
        engine_config=profile.engine_config,
        policy_rules=profile.policy_rules,
    )


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
    profile = await _resolve_profile(session, tenant, payload.profile_id)
    pipeline = _pipeline_for(profile, settings, client, default_pipeline)
    service = ModerationService(pipeline, settings)
    return await service.moderate(payload, session=session, tenant=tenant, profile=profile)


@router.post(
    "/moderate/batch",
    response_model=BatchModerationResponse,
    summary="Moderar un lote de comentarios",
)
async def moderate_batch(
    payload: BatchModerationRequest,
    api_key: ModerateKeyParam,
    _: RateLimitParam,
    session: SessionParam,
    settings: SettingsParam,
    client: HttpClientParam,
    default_pipeline: PipelineParam,
) -> BatchModerationResponse:
    """Modera hasta 100 comentarios con el mismo perfil."""
    tenant = api_key.tenant
    profile = await _resolve_profile(session, tenant, payload.profile_id)
    pipeline = _pipeline_for(profile, settings, client, default_pipeline)
    service = ModerationService(pipeline, settings)
    results = await service.moderate_batch(
        payload.items, session=session, tenant=tenant, profile=profile
    )
    return BatchModerationResponse(count=len(results), results=results)
