"""Normalización de texto no confiable antes de clasificarlo."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass

_WHITESPACE = " \t\r\n\f\v"


@dataclass(slots=True)
class NormalizedText:
    """Resultado de normalizar un comentario."""

    text: str
    original_length: int
    truncated: bool
    removed_chars: int


def _is_removable(char: str) -> bool:
    category = unicodedata.category(char)
    if category == "Cf":
        return True
    return category == "Cc" and char not in _WHITESPACE


def normalize_text(text: str, *, max_length: int = 5000) -> NormalizedText:
    """Normaliza Unicode, elimina caracteres invisibles y acota la longitud."""
    original_length = len(text)
    decomposed = unicodedata.normalize("NFKC", text)

    kept: list[str] = []
    removed = 0
    for char in decomposed:
        if _is_removable(char):
            removed += 1
            continue
        kept.append(char)

    cleaned = " ".join("".join(kept).split())
    truncated = len(cleaned) > max_length
    if truncated:
        cleaned = cleaned[:max_length]

    return NormalizedText(
        text=cleaned,
        original_length=original_length,
        truncated=truncated,
        removed_chars=removed,
    )
