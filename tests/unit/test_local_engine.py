"""Tests del motor local de embeddings (con modelo inyectado)."""

from __future__ import annotations

import builtins
from typing import Any

import pytest

from aimoderator.core.errors import EngineError
from aimoderator.engines.base import ClassificationRequest
from aimoderator.engines.local_ml import LocalMLEngine
from aimoderator.schemas.common import Category


class _StubModel:
    """Asigna vectores 2D simples según palabras clave."""

    def encode(self, texts: list[str], normalize_embeddings: bool = False) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            lowered = text.lower()
            if "idiota" in lowered or "insult" in lowered:
                vectors.append([1.0, 0.0])
            elif "lastimar" in lowered or "amenaz" in lowered:
                vectors.append([0.0, 1.0])
            else:
                vectors.append([0.5, 0.5])
        return vectors


async def test_scores_by_similarity() -> None:
    engine = LocalMLEngine(model_name="stub", model=_StubModel())
    result = await engine.classify(
        ClassificationRequest(
            text="sos un idiota", categories=[Category.TOXICITY, Category.HARASSMENT]
        )
    )
    assert result.scores["toxicity"] == 1.0
    assert result.scores["harassment"] < result.scores["toxicity"]
    assert result.engine == "local"


async def test_missing_dependency_raises_engine_error(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = builtins.__import__

    def fake_import(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "sentence_transformers":
            raise ImportError("no disponible")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    engine = LocalMLEngine(model_name="modelo-inexistente")
    with pytest.raises(EngineError):
        await engine.classify(ClassificationRequest(text="hola"))
