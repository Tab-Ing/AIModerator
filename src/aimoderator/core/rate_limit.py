"""Limitador de tasa en memoria (ventana deslizante).

Nota: es un límite **por proceso**; en despliegues con varias réplicas se debe
complementar con un backend compartido (p. ej. Redis). Las cuotas diarias sí se
llevan en PostgreSQL vía ``usage_counters``.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from functools import lru_cache
from threading import Lock


class SlidingWindowRateLimiter:
    """Permite hasta ``limit`` eventos por clave en una ventana de tiempo."""

    def __init__(self, limit: int, window_seconds: float = 60.0) -> None:
        self._limit = limit
        self._window = window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    @property
    def limit(self) -> int:
        return self._limit

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        with self._lock:
            events = self._events[key]
            while events and now - events[0] > self._window:
                events.popleft()
            if len(events) >= self._limit:
                return False
            events.append(now)
            return True

    def reset(self) -> None:
        with self._lock:
            self._events.clear()


@lru_cache(maxsize=8)
def get_rate_limiter(limit: int) -> SlidingWindowRateLimiter:
    """Devuelve el limitador cacheado para un límite dado."""
    return SlidingWindowRateLimiter(limit)
