"""Entorno de plantillas y estáticos del panel."""

from __future__ import annotations

from pathlib import Path

from fastapi.templating import Jinja2Templates

ADMIN_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = ADMIN_DIR / "templates"
STATIC_DIR = ADMIN_DIR / "static"

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
