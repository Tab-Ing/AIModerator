"""Pipeline de moderación: normalizar → guard PI → motor → política."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

from aimoderator.config import Settings
from aimoderator.engines.base import ClassificationEngine, ClassificationRequest
from aimoderator.engines.heuristic import HeuristicEngine
from aimoderator.engines.jev import JevEngine
from aimoderator.engines.registry import EngineRegistry
from aimoderator.moderation.normalizer import normalize_text
from aimoderator.moderation.policy import PolicyEngine
from aimoderator.moderation.prompt_injection import InjectionAssessment, PromptInjectionGuard
from aimoderator.schemas.common import DEFAULT_CATEGORIES, Action, Category

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ModerationDecision:
    """Decisión interna del pipeline (incluye texto normalizado para redacción)."""

    action: Action
    categories: list[str]
    scores: dict[str, float]
    engine: str
    injection_detected: bool
    reasons: list[str] = field(default_factory=list)
    confidence: float | None = None
    latency_ms: int = 0
    normalized_text: str = ""
    text_truncated: bool = False


class ModerationPipeline:
    """Orquesta las etapas de moderación de forma determinista."""

    def __init__(
        self,
        *,
        engine: ClassificationEngine,
        guard: PromptInjectionGuard,
        policy: PolicyEngine,
        max_text_length: int = 5000,
        short_circuit: bool = True,
        use_pi_guard: bool = True,
    ) -> None:
        self._engine = engine
        self._guard = guard
        self._policy = policy
        self._max_text_length = max_text_length
        self._short_circuit = short_circuit
        self._use_pi_guard = use_pi_guard

    async def run(
        self,
        text: str,
        *,
        locale: str | None = None,
        platform: str | None = None,
    ) -> ModerationDecision:
        started = time.perf_counter()
        normalized = normalize_text(text, max_length=self._max_text_length)
        assessment = (
            self._guard.assess(normalized.text)
            if self._use_pi_guard
            else InjectionAssessment(detected=False, score=0.0)
        )
        reasons = list(assessment.reasons)

        if self._short_circuit and assessment.detected:
            return ModerationDecision(
                action=Action.BLOCK,
                categories=[Category.PROMPT_INJECTION.value],
                scores={Category.PROMPT_INJECTION.value: assessment.score},
                engine="guard",
                injection_detected=True,
                reasons=reasons,
                confidence=assessment.score,
                latency_ms=self._elapsed_ms(started),
                normalized_text=normalized.text,
                text_truncated=normalized.truncated,
            )

        result = await self._engine.classify(
            ClassificationRequest(
                text=normalized.text,
                locale=locale,
                platform=platform,
                categories=list(DEFAULT_CATEGORIES),
            )
        )

        scores = dict(result.scores)
        current = scores.get(Category.PROMPT_INJECTION.value, 0.0)
        if assessment.score > current:
            scores[Category.PROMPT_INJECTION.value] = assessment.score

        evaluation = self._policy.evaluate(scores)
        injection_detected = assessment.detected or (
            scores.get(Category.PROMPT_INJECTION.value, 0.0) >= self._guard.threshold
        )

        return ModerationDecision(
            action=evaluation.action,
            categories=evaluation.categories,
            scores=scores,
            engine=result.engine,
            injection_detected=injection_detected,
            reasons=reasons,
            confidence=result.confidence,
            latency_ms=self._elapsed_ms(started),
            normalized_text=normalized.text,
            text_truncated=normalized.truncated,
        )

    @staticmethod
    def _elapsed_ms(started: float) -> int:
        return max(0, round((time.perf_counter() - started) * 1000))


def build_engine_registry(settings: Settings, client: httpx.AsyncClient) -> EngineRegistry:
    """Registra los motores disponibles según la configuración."""
    registry = EngineRegistry()
    registry.register(HeuristicEngine())

    if settings.jev_enabled and settings.jev_api_key:
        registry.register(
            JevEngine(
                client=client,
                base_url=settings.jev_base_url,
                model=settings.jev_model,
                api_key=settings.jev_api_key,
                timeout=settings.engine_timeout_seconds,
            )
        )
    return registry


def build_pipeline(
    settings: Settings,
    client: httpx.AsyncClient,
    *,
    engine_config: dict[str, Any] | None = None,
    policy_rules: dict[str, Any] | None = None,
) -> ModerationPipeline:
    """Construye el pipeline según la config del perfil (o los valores por defecto)."""
    registry = build_engine_registry(settings, client)

    config: dict[str, Any] = engine_config or {}
    engine_name = str(config.get("primary") or settings.default_engine)
    if not registry.has(engine_name):
        logger.warning("Motor '%s' no disponible; se usa 'heuristic'", engine_name)
        engine_name = "heuristic"
    engine = registry.get(engine_name)

    return ModerationPipeline(
        engine=engine,
        guard=PromptInjectionGuard(threshold=settings.pi_threshold),
        policy=PolicyEngine(policy_rules),
        max_text_length=settings.max_text_length,
        short_circuit=settings.pi_short_circuit,
        use_pi_guard=bool(config.get("use_pi_guard", True)),
    )
