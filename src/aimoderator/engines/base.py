"""Interfaz común de motores de clasificación."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from aimoderator.schemas.common import Action, Category


@dataclass(slots=True)
class ClassificationRequest:
    """Entrada de un motor: el comentario se trata SIEMPRE como dato no confiable."""

    text: str
    locale: str | None = None
    platform: str | None = None
    categories: list[Category] = field(default_factory=list)
    options: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ClassificationResult:
    """Salida normalizada de cualquier motor."""

    engine: str
    scores: dict[str, float] = field(default_factory=dict)
    action: Action | None = None
    confidence: float | None = None
    injection_detected: bool = False
    raw: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class ClassificationEngine(Protocol):
    """Contrato que cumplen todos los motores (Jev, LLM, local, heurístico)."""

    name: str

    async def classify(self, request: ClassificationRequest) -> ClassificationResult:
        """Clasifica un comentario y devuelve scores/acción normalizados."""
        ...
