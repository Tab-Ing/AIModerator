"""Tests de generación y verificación de API keys."""

from __future__ import annotations

from aimoderator.core.security import generate_api_key, hash_api_key, verify_api_key


def test_generate_api_key_has_prefix() -> None:
    key = generate_api_key()
    assert key.startswith("aim_")
    assert len(key) > 20


def test_hash_is_deterministic() -> None:
    key = "aim_test_key"
    assert hash_api_key(key) == hash_api_key(key)


def test_verify_api_key() -> None:
    key = generate_api_key()
    assert verify_api_key(key, hash_api_key(key))
    assert not verify_api_key("aim_wrong", hash_api_key(key))
