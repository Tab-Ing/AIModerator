"""Middleware de correlación de solicitudes, logging de acceso y métricas."""

from __future__ import annotations

import logging
import time
import uuid

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from aimoderator.core import metrics

logger = logging.getLogger("aimoderator.access")


def _route_path(request: Request) -> str:
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    return path if isinstance(path, str) else request.url.path


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Agrega ``X-Request-ID``, registra el acceso y alimenta las métricas."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        request.state.request_id = request_id
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            metrics.HTTP_REQUESTS.labels(request.method, _route_path(request), "500").inc()
            logger.exception(
                "request_id=%s method=%s path=%s status=500",
                request_id,
                request.method,
                request.url.path,
            )
            raise

        duration = time.perf_counter() - started
        path = _route_path(request)
        metrics.HTTP_LATENCY.labels(request.method, path).observe(duration)
        metrics.HTTP_REQUESTS.labels(request.method, path, str(response.status_code)).inc()
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request_id=%s method=%s path=%s status=%s duration_ms=%d",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            round(duration * 1000),
        )
        return response


def register_middleware(app: FastAPI) -> None:
    app.add_middleware(RequestContextMiddleware)
