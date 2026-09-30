"""Tests del normalizador de texto."""

from __future__ import annotations

from aimoderator.moderation.normalizer import normalize_text


def test_removes_zero_width_and_format_chars() -> None:
    result = normalize_text("ho\u200b\u200dla")
    assert result.text == "hola"
    assert result.removed_chars == 2


def test_removes_bidi_control_chars() -> None:
    result = normalize_text("texto\u202eoculto")
    assert "\u202e" not in result.text


def test_applies_nfkc_normalization() -> None:
    result = normalize_text("ﬁn")
    assert result.text == "fin"


def test_collapses_whitespace() -> None:
    result = normalize_text("hola\t\n   mundo")
    assert result.text == "hola mundo"


def test_truncates_long_text() -> None:
    result = normalize_text("a" * 100, max_length=10)
    assert result.truncated is True
    assert len(result.text) == 10


def test_keeps_original_length() -> None:
    result = normalize_text("hola")
    assert result.original_length == 4
    assert result.truncated is False
