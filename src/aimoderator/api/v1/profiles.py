"""Endpoints de perfiles de uso."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, status

from aimoderator.api.deps import ProfilesReadKeyParam, ProfilesWriteKeyParam, SessionParam
from aimoderator.schemas.profile import ProfileCreate, ProfileRead, ProfileUpdate
from aimoderator.services.profile_service import ProfileService

router = APIRouter(tags=["perfiles"])


@router.get("/profiles", response_model=list[ProfileRead], summary="Listar perfiles")
async def list_profiles(api_key: ProfilesReadKeyParam, session: SessionParam) -> list[ProfileRead]:
    profiles = await ProfileService().list(session, api_key.tenant_id)
    return [ProfileRead.model_validate(profile) for profile in profiles]


@router.post(
    "/profiles",
    response_model=ProfileRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear perfil de uso",
)
async def create_profile(
    payload: ProfileCreate, api_key: ProfilesWriteKeyParam, session: SessionParam
) -> ProfileRead:
    profile = await ProfileService().create(
        session, api_key.tenant_id, payload, actor=api_key.label or api_key.prefix
    )
    return ProfileRead.model_validate(profile)


@router.get("/profiles/{profile_id}", response_model=ProfileRead, summary="Obtener perfil")
async def get_profile(
    profile_id: UUID, api_key: ProfilesReadKeyParam, session: SessionParam
) -> ProfileRead:
    profile = await ProfileService().get(session, api_key.tenant_id, profile_id)
    return ProfileRead.model_validate(profile)


@router.patch("/profiles/{profile_id}", response_model=ProfileRead, summary="Actualizar perfil")
async def update_profile(
    profile_id: UUID,
    payload: ProfileUpdate,
    api_key: ProfilesWriteKeyParam,
    session: SessionParam,
) -> ProfileRead:
    profile = await ProfileService().update(
        session, api_key.tenant_id, profile_id, payload, actor=api_key.label or api_key.prefix
    )
    return ProfileRead.model_validate(profile)


@router.delete(
    "/profiles/{profile_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar perfil",
)
async def delete_profile(
    profile_id: UUID, api_key: ProfilesWriteKeyParam, session: SessionParam
) -> None:
    await ProfileService().delete(
        session, api_key.tenant_id, profile_id, actor=api_key.label or api_key.prefix
    )


@router.post(
    "/profiles/{profile_id}/activate",
    response_model=ProfileRead,
    summary="Activar perfil",
)
async def activate_profile(
    profile_id: UUID, api_key: ProfilesWriteKeyParam, session: SessionParam
) -> ProfileRead:
    profile = await ProfileService().activate(
        session, api_key.tenant_id, profile_id, actor=api_key.label or api_key.prefix
    )
    return ProfileRead.model_validate(profile)
