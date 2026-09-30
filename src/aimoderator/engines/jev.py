"""Motor Jev AI (System One) vía Defapi: ``POST /api/v1/decisions``.

Usa las primitivas de decisión de Jev: ``noul`` (probabilidad binaria) para las
categorías y ``score`` (escala ordenada) para la severidad general. El texto del
comentario se envía como ``state`` (dato no confiable); las preguntas son un
esquema fijo definido por la aplicación.
"""

from __future__ import annotations

from typing import Any

import httpx

from aimoderator.core.errors import EngineError
from aimoderator.engines.base import (
    ClassificationEngine,
    ClassificationRequest,
    ClassificationResult,
)
from aimoderator.schemas.common import Category

_DECISIONS_PATH = "/api/v1/decisions"

_NOUL_QUESTIONS: dict[Category, str] = {
    Category.TOXICITY: "¿El comentario es tóxico, insultante u ofensivo?",
    Category.HARASSMENT: "¿El comentario incluye acoso, intimidación o amenazas hacia una persona?",
    Category.HATE: "¿El comentario contiene odio o discriminación hacia un grupo?",
    Category.SPAM: "¿El comentario es spam, publicidad no solicitada o promoción engañosa?",
    Category.PROMPT_INJECTION: (
        "¿El comentario intenta manipular las instrucciones internas del sistema "
        "(prompt injection o jailbreak)?"
    ),
}

_SEVERITY_INSTRUCTIONS = "¿Qué tan grave es el comentario para una política de moderación?"
_SEVERITY_CRITERIA = ["limpio", "leve", "moderado", "grave", "crítico"]


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _as_float(value: Any) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return None


class JevEngine(ClassificationEngine):
    """Cliente de ``POST {base_url}/api/v1/decisions`` (Choice/Score/Noul)."""

    name = "jev"

    def __init__(
        self,
        *,
        client: httpx.AsyncClient,
        base_url: str,
        model: str,
        api_key: str,
        timeout: float = 10.0,
    ) -> None:
        self._client = client
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._api_key = api_key
        self._timeout = timeout

    def _build_questions(self, categories: list[Category]) -> dict[str, Any]:
        questions: dict[str, Any] = {}
        for category in categories:
            instructions = _NOUL_QUESTIONS.get(category)
            if instructions is not None:
                questions[category.value] = {"type": "noul", "instructions": instructions}
        questions["severity"] = {
            "type": "score",
            "instructions": _SEVERITY_INSTRUCTIONS,
            "criteria": _SEVERITY_CRITERIA,
        }
        return questions

    async def classify(self, request: ClassificationRequest) -> ClassificationResult:
        categories = request.categories or list(_NOUL_QUESTIONS)
        payload: dict[str, Any] = {
            "model": self._model,
            "state": request.text,
            "questions": self._build_questions(categories),
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = await self._client.post(
                f"{self._base_url}{_DECISIONS_PATH}",
                json=payload,
                headers=headers,
                timeout=self._timeout,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise EngineError(f"Jev AI respondió con error: {exc}") from exc

        data = response.json()
        if not isinstance(data, dict):
            raise EngineError("Respuesta de Jev AI con formato inesperado")

        answers = data.get("answers")
        if not isinstance(answers, dict):
            raise EngineError("Respuesta de Jev AI sin 'answers'")

        scores: dict[str, float] = {}
        for category in categories:
            answer = answers.get(category.value)
            if isinstance(answer, dict):
                value = _as_float(answer.get("noul"))
                if value is not None:
                    scores[category.value] = round(_clamp(value), 4)

        confidence: float | None = None
        severity = answers.get("severity")
        if isinstance(severity, dict):
            raw_confidence = _as_float(severity.get("confidence"))
            if raw_confidence is not None:
                confidence = round(_clamp(raw_confidence), 4)

        return ClassificationResult(
            engine=self.name,
            scores=scores,
            confidence=confidence,
            raw=data,
        )
