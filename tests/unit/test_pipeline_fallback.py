"""Tests de fallback y consenso entre motores."""

from __future__ import annotations

import httpx

from aimoderator.config import Settings
from aimoderator.core.errors import EngineError
from aimoderator.engines.base import (
    ClassificationEngine,
    ClassificationRequest,
    ClassificationResult,
)
from aimoderator.moderation.pipeline import ModerationPipeline, build_engine_registry
from aimoderator.moderation.policy import PolicyEngine
from aimoderator.moderation.prompt_injection import PromptInjectionGuard


class _FailingEngine(ClassificationEngine):
    name = "failing"

    async def classify(self, request: ClassificationRequest) -> ClassificationResult:
        raise EngineError("boom")


class _FixedEngine(ClassificationEngine):
    name = "fixed"

    def __init__(self, score: float) -> None:
        self._score = score

    async def classify(self, request: ClassificationRequest) -> ClassificationResult:
        return ClassificationResult(engine=self.name, scores={"toxicity": self._score})


def _pipeline(
    engine: ClassificationEngine,
    *,
    fallbacks: list[ClassificationEngine] | None = None,
    consensus: bool = False,
) -> ModerationPipeline:
    return ModerationPipeline(
        engine=engine,
        guard=PromptInjectionGuard(),
        policy=PolicyEngine(),
        fallbacks=fallbacks,
        consensus=consensus,
    )


async def test_fallback_on_engine_error() -> None:
    decision = await _pipeline(_FailingEngine(), fallbacks=[_FixedEngine(0.9)]).run("hola")
    assert decision.engine == "fixed"
    assert decision.scores["toxicity"] == 0.9


async def test_fallback_exhausted_raises() -> None:
    pipeline = _pipeline(_FailingEngine(), fallbacks=[_FailingEngine()])
    try:
        await pipeline.run("hola")
    except EngineError:
        pass
    else:  # pragma: no cover
        raise AssertionError("se esperaba EngineError")


async def test_consensus_merges_max_scores() -> None:
    decision = await _pipeline(
        _FixedEngine(0.2), fallbacks=[_FixedEngine(0.8)], consensus=True
    ).run("hola")
    assert decision.engine.startswith("consensus:")
    assert decision.scores["toxicity"] == 0.8


async def test_registry_registers_optional_engines() -> None:
    settings = Settings(llm_enabled=True, llm_api_key="k", local_enabled=True)
    async with httpx.AsyncClient() as client:
        registry = build_engine_registry(settings, client)
    assert registry.has("heuristic")
    assert registry.has("llm")
    assert registry.has("local")
