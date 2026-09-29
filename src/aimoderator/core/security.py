"""Utilidades de seguridad: generación y verificación de API keys.

Las API keys nunca se almacenan en claro: se guarda su hash con pepper
(``AIMODERATOR_SECRET_KEY``). Comparación en tiempo constante.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

from aimoderator.config import get_settings

_TOKEN_BYTES = 32


def generate_api_key() -> str:
    """Genera una API key nueva con el prefijo configurado."""
    settings = get_settings()
    return f"{settings.api_key_prefix}{secrets.token_urlsafe(_TOKEN_BYTES)}"


def hash_api_key(raw_key: str) -> str:
    """Devuelve el hash SHA-256 de la API key con el pepper del proyecto."""
    pepper = get_settings().secret_key.encode("utf-8")
    return hashlib.sha256(pepper + raw_key.encode("utf-8")).hexdigest()


def verify_api_key(raw_key: str, hashed_key: str) -> bool:
    """Compara una API key con su hash en tiempo constante."""
    return hmac.compare_digest(hash_api_key(raw_key), hashed_key)
