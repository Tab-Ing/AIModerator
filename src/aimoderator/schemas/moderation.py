"""Esquemas de entrada/salida de moderación."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import Field

from aimoderator.schemas.common import Action, APIModel, Category


class ModerationRequest(APIModel):
    """Comentario a moderar. El texto se trata como dato no confiable."""

    text: str = Field(min_length=1, max_length=20000)
    profile_id: UUID | None = None
    external_id: str | None = Field(default=None, max_length=255)
    platform: str | None = Field(default=None, max_length=50)
    locale: str | None = Field(default=None, max_length=20)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ModerationResponse(APIModel):
    """Decisión de moderación normalizada."""

    record_id: UUID | None = None
    action: Action
    categories: list[Category] = Field(default_factory=list)
    scores: dict[str, float] = Field(default_factory=dict)
    confidence: float | None = None
    engine: str
    injection_detected: bool = False
    text_truncated: bool = False
    reasons: list[str] = Field(default_factory=list)
    latency_ms: int = 0
