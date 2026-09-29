"""Configuración de logging estructurado."""

from __future__ import annotations

import logging
import sys

_CONFIGURED = False


def configure_logging(level: str = "INFO") -> None:
    """Configura el logger raíz una sola vez."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
    )
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.upper())
    _CONFIGURED = True
