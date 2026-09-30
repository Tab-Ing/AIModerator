"""Motor heurístico basado en listas de patrones (sin costo, determinista)."""

from __future__ import annotations

import re

from aimoderator.engines.base import (
    ClassificationEngine,
    ClassificationRequest,
    ClassificationResult,
)
from aimoderator.schemas.common import Category

_LEXICON: dict[Category, tuple[tuple[re.Pattern[str], float], ...]] = {
    Category.TOXICITY: (
        (
            re.compile(r"\b(idiot|stupid|moron|imbecil|imbécil|idiota|estupido|estúpido)\b", re.I),
            0.7,
        ),
        (re.compile(r"\b(basura|scum|trash)\b", re.I), 0.6),
    ),
    Category.HARASSMENT: (
        (re.compile(r"\b(kill yourself|kys|muere|ojala te mueras|ojalá te mueras)\b", re.I), 0.95),
        (re.compile(r"\b(we will find you|te vamos a encontrar)\b", re.I), 0.85),
    ),
    Category.HATE: (
        (re.compile(r"\b(nazi|supremacist|supremacista)\b", re.I), 0.6),
        (
            re.compile(
                r"\b(all|todos los)\s+\w+\s+(should die|deberian morir|deberían morir)\b", re.I
            ),
            0.9,
        ),
    ),
    Category.SPAM: (
        (
            re.compile(
                r"(free money|gana dinero facil|ganá dinero fácil|click here"
                r"|haz clic aqui|haz clic aquí|buy now|compra ya)",
                re.I,
            ),
            0.7,
        ),
        (re.compile(r"(?:https?://\S+\s*){3,}", re.I), 0.6),
        (re.compile(r"\b(casino|crypto giveaway|sorteo gratis)\b", re.I), 0.6),
    ),
}


class HeuristicEngine(ClassificationEngine):
    """Clasifica por coincidencia de patrones; puntaje = mayor peso hallado."""

    name = "heuristic"

    async def classify(self, request: ClassificationRequest) -> ClassificationResult:
        categories = request.categories or list(_LEXICON)
        scores: dict[str, float] = {}
        for category in categories:
            patterns = _LEXICON.get(category, ())
            score = 0.0
            for pattern, weight in patterns:
                if pattern.search(request.text):
                    score = max(score, weight)
            scores[category.value] = round(score, 4)

        return ClassificationResult(engine=self.name, scores=scores, raw={"source": "lexicon"})
