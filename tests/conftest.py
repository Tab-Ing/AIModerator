"""Fixtures compartidas de pytest."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from aimoderator.main import create_app


@pytest.fixture()
def app() -> FastAPI:
    """Aplicación FastAPI configurada para tests."""
    return create_app()


@pytest.fixture()
def client(app: FastAPI) -> TestClient:
    """Cliente HTTP de tests."""
    return TestClient(app)
