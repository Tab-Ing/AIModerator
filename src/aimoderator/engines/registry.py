"""Registro de motores de clasificación disponibles."""

from __future__ import annotations

from aimoderator.core.errors import EngineError
from aimoderator.engines.base import ClassificationEngine


class EngineRegistry:
    """Mantiene el conjunto de motores instanciados por nombre."""

    def __init__(self) -> None:
        self._engines: dict[str, ClassificationEngine] = {}

    def register(self, engine: ClassificationEngine) -> None:
        self._engines[engine.name] = engine

    def get(self, name: str) -> ClassificationEngine:
        try:
            return self._engines[name]
        except KeyError as exc:
            raise EngineError(f"Motor desconocido: {name}") from exc

    def has(self, name: str) -> bool:
        return name in self._engines

    @property
    def names(self) -> list[str]:
        return sorted(self._engines)
