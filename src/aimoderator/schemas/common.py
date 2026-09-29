"""Esquemas y enumeraciones comunes."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class Action(StrEnum):
    """Acción de moderación a aplicar sobre un comentario."""

    ALLOW = "allow"
    FLAG = "flag"
    HIDE = "hide"
    BLOCK = "block"
    ESCALATE = "escalate"


class Category(StrEnum):
    """Categorías de clasificación soportadas."""

    TOXICITY = "toxicity"
    HARASSMENT = "harassment"
    HATE = "hate"
    SPAM = "spam"
    PROMPT_INJECTION = "prompt_injection"


class Plan(StrEnum):
    """Modelo de licencia/plan de un tenant."""

    FREE = "free"
    COMMERCIAL = "commercial"


class APIModel(BaseModel):
    """Base para esquemas de entrada/salida de la API."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")
