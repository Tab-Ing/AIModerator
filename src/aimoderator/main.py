"""Punto de entrada de la aplicación FastAPI."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from aimoderator import __version__
from aimoderator.api.v1.router import api_router
from aimoderator.config import Settings, get_settings
from aimoderator.core.errors import install_exception_handlers
from aimoderator.core.logging import configure_logging
from aimoderator.moderation.pipeline import build_pipeline

DESCRIPTION = (
    "API multi-tenant para moderar comentarios de redes sociales. "
    "Cada empresa define perfiles de uso (política de bloqueo + motor) y "
    "la API protege frente a prompt injection en los mensajes."
)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Crea y configura la aplicación FastAPI."""
    app_settings = settings or get_settings()
    configure_logging(app_settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        client = httpx.AsyncClient()
        app.state.http_client = client
        app.state.pipeline = build_pipeline(app_settings, client)
        try:
            yield
        finally:
            await client.aclose()

    app = FastAPI(
        title="AIModerator API",
        version=__version__,
        description=DESCRIPTION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    install_exception_handlers(app)
    app.include_router(api_router, prefix="/v1")

    @app.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        return {
            "name": "aimoderator",
            "version": __version__,
            "docs": "/docs",
        }

    return app


app = create_app()


def run() -> None:
    """Entrypoint de consola (``aimoderator``)."""
    import uvicorn

    settings = get_settings()
    uvicorn.run("aimoderator.main:app", host=settings.host, port=settings.port)
