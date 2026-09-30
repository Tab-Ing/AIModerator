"""Esquemas de los perfiles de uso (política de bloqueo + motor)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from aimoderator.moderation.policy import DEFAULT_POLICY
from aimoderator.schemas.common import Action, APIModel, Category


def _default_thresholds() -> dict[Category, float]:
    raw = DEFAULT_POLICY["thresholds"]
    return {Category(key): float(value) for key, value in raw.items()}


def _default_actions() -> dict[Category, Action]:
    raw = DEFAULT_POLICY["actions"]
    return {Category(key): Action(value) for key, value in raw.items()}


class EngineConfig(APIModel):
    """Selección del motor/modelo a usar por el perfil."""

    primary: str = Field(default="heuristic", min_length=1, max_length=50)
    fallbacks: list[str] = Field(default_factory=list)
    consensus: bool = False
    use_pi_guard: bool = True
    options: dict[str, Any] = Field(default_factory=dict)


class PolicyRules(APIModel):
    """Política de bloqueo: umbrales por categoría y acción asociada."""

    thresholds: dict[Category, float] = Field(default_factory=_default_thresholds)
    actions: dict[Category, Action] = Field(default_factory=_default_actions)
    default_action: Action = Action.ALLOW


class ProfileCreate(APIModel):
    """Cuerpo para crear un perfil de uso."""

    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=2000)
    engine_config: EngineConfig = Field(default_factory=EngineConfig)
    policy_rules: PolicyRules = Field(default_factory=PolicyRules)


class ProfileUpdate(APIModel):
    """Cuerpo para actualizar un perfil (parcial)."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=2000)
    engine_config: EngineConfig | None = None
    policy_rules: PolicyRules | None = None


class ProfileRead(APIModel):
    """Representación de un perfil de uso."""

    id: UUID
    name: str
    description: str | None = None
    engine_config: EngineConfig
    policy_rules: PolicyRules
    version: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
