"""Fixtures compartidas de pytest."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from aimoderator.main import create_app


@pytest.fixture()
def app() -> FastAPI:
    """Aplicación FastAPI configurada para tests."""
    return create_app()


@pytest.fixture()
def client(app: FastAPI) -> Iterator[TestClient]:
    """Cliente HTTP de tests (ejecuta el lifespan de la app)."""
    with TestClient(app) as test_client:
        yield test_client
