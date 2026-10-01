"""Errores de dominio y manejadores HTTP."""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class AIModeratorError(Exception):
    """Error base de la aplicación."""

    status_code = status.HTTP_400_BAD_REQUEST
    code = "aimoderator_error"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code


class NotFoundError(AIModeratorError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "not_found"


class UnauthorizedError(AIModeratorError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "unauthorized"


class ForbiddenError(AIModeratorError):
    status_code = status.HTTP_403_FORBIDDEN
    code = "forbidden"


class RateLimitError(AIModeratorError):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    code = "rate_limited"


class QuotaExceededError(AIModeratorError):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    code = "quota_exceeded"


class QueueUnavailableError(AIModeratorError):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    code = "queue_unavailable"


class EngineError(AIModeratorError):
    status_code = status.HTTP_502_BAD_GATEWAY
    code = "engine_error"


def install_exception_handlers(app: FastAPI) -> None:
    """Registra los manejadores de excepciones de dominio."""

    @app.exception_handler(AIModeratorError)
    async def _handle_domain_error(_: Request, exc: AIModeratorError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )
