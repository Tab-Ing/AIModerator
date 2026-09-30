"""Motor Jev AI (System One Model) vía la API de decisiones tipadas."""

from __future__ import annotations

from typing import Any

import httpx

from aimoderator.core.errors import EngineError
from aimoderator.engines.base import (
    ClassificationEngine,
    ClassificationRequest,
    ClassificationResult,
)
from aimoderator.schemas.common import Action, Category

_DECIDE_PATH = "/v1/decide"


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


class JevEngine(ClassificationEngine):
    """Cliente de ``POST {base_url}/v1/decide`` con esquema numérico por categoría."""

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

    async def classify(self, request: ClassificationRequest) -> ClassificationResult:
        categories = request.categories or [Category.PROMPT_INJECTION]
        schema = {category.value: "number" for category in categories}
        payload: dict[str, Any] = {
            "model": self._model,
            "input": request.text,
            "schema": schema,
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = await self._client.post(
                f"{self._base_url}{_DECIDE_PATH}",
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

        scores: dict[str, float] = {}
        for category in categories:
            value = data.get(category.value)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                scores[category.value] = round(_clamp(float(value)), 4)

        confidence = data.get("confidence")
        action_value = data.get("action")
        action = Action(action_value) if action_value in set(Action) else None

        return ClassificationResult(
            engine=self.name,
            scores=scores,
            action=action,
            confidence=float(confidence) if isinstance(confidence, (int, float)) else None,
            raw=data,
        )
