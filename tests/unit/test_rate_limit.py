"""Tests del limitador de tasa en memoria."""

from __future__ import annotations

from aimoderator.core.rate_limit import SlidingWindowRateLimiter


def test_allows_up_to_limit() -> None:
    limiter = SlidingWindowRateLimiter(limit=3, window_seconds=60)
    assert [limiter.allow("k") for _ in range(4)] == [True, True, True, False]


def test_keys_are_independent() -> None:
    limiter = SlidingWindowRateLimiter(limit=1, window_seconds=60)
    assert limiter.allow("a") is True
    assert limiter.allow("b") is True
    assert limiter.allow("a") is False


def test_reset_clears_state() -> None:
    limiter = SlidingWindowRateLimiter(limit=1, window_seconds=60)
    assert limiter.allow("k") is True
    limiter.reset()
    assert limiter.allow("k") is True
