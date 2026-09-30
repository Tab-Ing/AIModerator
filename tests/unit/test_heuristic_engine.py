"""Tests del motor heurístico."""

from __future__ import annotations

from aimoderator.engines.base import ClassificationRequest
from aimoderator.engines.heuristic import HeuristicEngine


async def test_detects_toxicity() -> None:
    result = await HeuristicEngine().classify(ClassificationRequest(text="sos un idiota"))
    assert result.scores["toxicity"] >= 0.7


async def test_detects_harassment() -> None:
    result = await HeuristicEngine().classify(ClassificationRequest(text="kill yourself"))
    assert result.scores["harassment"] >= 0.9


async def test_detects_spam() -> None:
    result = await HeuristicEngine().classify(ClassificationRequest(text="gana dinero facil ahora"))
    assert result.scores["spam"] >= 0.6


async def test_benign_text_scores_zero() -> None:
    result = await HeuristicEngine().classify(
        ClassificationRequest(text="Excelente atención, muchas gracias")
    )
    assert result.scores["toxicity"] == 0
    assert result.scores["harassment"] == 0
    assert result.engine == "heuristic"
