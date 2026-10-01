"""Esquemas de trabajos asíncronos."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from aimoderator.schemas.common import APIModel
from aimoderator.schemas.moderation import ModerationRequest


class BatchJobRequest(APIModel):
    """Solicitud de lote asíncrono (se encola y devuelve un job id)."""

    profile_id: str | None = None
    items: list[ModerationRequest] = Field(min_length=1, max_length=100)


class JobAcceptedResponse(APIModel):
    job_id: str
    status: str


class JobStatusResponse(APIModel):
    job_id: str
    status: str
    result: dict[str, Any] | None = None
