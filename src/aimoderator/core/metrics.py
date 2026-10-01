"""Métricas Prometheus de la aplicación."""

from __future__ import annotations

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    REGISTRY,
    Counter,
    Histogram,
    generate_latest,
)
from starlette.responses import Response

HTTP_REQUESTS = Counter(
    "aimoderator_http_requests_total",
    "Solicitudes HTTP por método, ruta y estado",
    ["method", "path", "status"],
)

HTTP_LATENCY = Histogram(
    "aimoderator_http_request_duration_seconds",
    "Duración de las solicitudes HTTP en segundos",
    ["method", "path"],
)

MODERATIONS = Counter(
    "aimoderator_moderations_total",
    "Moderaciones realizadas por motor, acción e inyección detectada",
    ["engine", "action", "injection"],
)


async def metrics_endpoint() -> Response:
    """Expone las métricas en formato Prometheus."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


def _counter_total(base_name: str) -> float:
    total = 0.0
    for metric in REGISTRY.collect():
        if metric.name == base_name:
            for sample in metric.samples:
                if sample.name == f"{base_name}_total":
                    total += sample.value
    return total


def snapshot() -> dict[str, float]:
    """Totales agregados para el panel de administración."""
    return {
        "moderations_total": _counter_total("aimoderator_moderations"),
        "http_requests_total": _counter_total("aimoderator_http_requests"),
    }
