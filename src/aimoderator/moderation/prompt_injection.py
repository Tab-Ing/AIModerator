"""Detección heurística de prompt injection / jailbreak."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_PATTERNS: tuple[tuple[str, float, re.Pattern[str]], ...] = (
    (
        "ignore_instructions",
        0.9,
        re.compile(
            r"\b(ignore|disregard|forget)\b[^.\n]{0,40}"
            r"\b(previous|prior|above|earlier|all)\b[^.\n]{0,20}"
            r"\b(instruction|prompt|rule)s?\b",
            re.IGNORECASE,
        ),
    ),
    (
        "ignore_instructions_es",
        0.9,
        re.compile(
            r"\b(ignora|ignorá|olvida|olvidá|descarta)\b[^.\n]{0,40}"
            r"\b(instrucciones|reglas|indicaciones|prompt)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "system_override",
        0.85,
        re.compile(r"(?:^|\n)\s*(system|assistant|developer|system prompt)\s*[:\-]", re.IGNORECASE),
    ),
    (
        "role_marker",
        0.9,
        re.compile(
            r"<\|?\s*(im_start|im_end|system|assistant|endoftext|start_header_id)\s*\|?>",
            re.IGNORECASE,
        ),
    ),
    (
        "identity_override",
        0.8,
        re.compile(
            r"\b(you are now|from now on|act as|pretend to be|behave as)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "identity_override_es",
        0.8,
        re.compile(
            r"\b(ahora sos|a partir de ahora|actua como|actúa como|fingí ser)\b", re.IGNORECASE
        ),
    ),
    (
        "jailbreak",
        0.85,
        re.compile(r"\b(jailbreak|dan mode|developer mode|do anything now)\b", re.IGNORECASE),
    ),
    (
        "prompt_exfiltration",
        0.85,
        re.compile(
            r"\b(repeat|reveal|print|show|leak|revela|repite|muestra)\b[^.\n]{0,30}"
            r"\b(system prompt|instructions|prompt|instrucciones)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "tool_invocation",
        0.8,
        re.compile(
            r"\b(call|invoke|execute|run|llama|ejecuta|invoca)\b[^.\n]{0,30}"
            r"\b(tool|function|command|herramienta|funcion|función|comando)s?\b",
            re.IGNORECASE,
        ),
    ),
)

_BASE64_RE = re.compile(r"\b[A-Za-z0-9+/]{20,}={0,2}\b")


@dataclass(slots=True)
class InjectionAssessment:
    """Veredicto del guard anti-prompt-injection."""

    detected: bool
    score: float
    reasons: list[str] = field(default_factory=list)
    suspicious: bool = False


class PromptInjectionGuard:
    """Aplica patrones de inyección conocidos sobre texto ya normalizado."""

    def __init__(self, threshold: float = 0.5) -> None:
        self._threshold = threshold

    @property
    def threshold(self) -> float:
        return self._threshold

    def assess(self, text: str) -> InjectionAssessment:
        reasons: list[str] = []
        score = 0.0
        for name, weight, pattern in _PATTERNS:
            if pattern.search(text):
                reasons.append(name)
                score = max(score, weight)

        suspicious = False
        if _BASE64_RE.search(text):
            suspicious = True
            reasons.append("encoded_blob")
            score = max(score, 0.4)

        return InjectionAssessment(
            detected=score >= self._threshold,
            score=round(score, 4),
            reasons=reasons,
            suspicious=suspicious,
        )
