"""Configuración central de la aplicación (12-factor, vía variables de entorno)."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración tipada cargada desde el entorno o un archivo .env."""

    model_config = SettingsConfigDict(
        env_prefix="AIMODERATOR_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: str = "development"
    log_level: str = "INFO"
    host: str = "0.0.0.0"
    port: int = 8000

    database_url: str = "postgresql+psycopg://aimoderator:aimoderator@localhost:55432/aimoderator"

    secret_key: str = "dev-insecure-change-me"
    api_key_prefix: str = "aim_"
    rate_limit_per_minute: int = 120
    free_plan_daily_quota: int = 1000
    commercial_plan_daily_quota: int = 100_000

    admin_username: str = "admin"
    admin_password: str = "admin"
    session_secret_key: str | None = None

    redis_url: str = "redis://localhost:56379/0"
    queue_enabled: bool = False

    jev_enabled: bool = False
    jev_base_url: str = "https://api.defapi.org"
    jev_model: str = "typesafe/jev-1.13"
    jev_api_key: str | None = None

    llm_enabled: bool = False
    llm_base_url: str = "https://api.deepseek.com"
    llm_chat_path: str = "/chat/completions"
    llm_model: str = "deepseek-flash"
    llm_api_key: str | None = None

    local_enabled: bool = False
    local_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    default_engine: str = "heuristic"
    engine_timeout_seconds: float = 10.0

    max_text_length: int = 5000
    store_redacted_text: bool = False
    redacted_text_max_chars: int = 500
    pi_short_circuit: bool = True
    pi_threshold: float = 0.5

    @property
    def is_production(self) -> bool:
        return self.env.lower() == "production"

    def session_key(self) -> str:
        """Clave para firmar la cookie de sesión del panel."""
        return self.session_secret_key or self.secret_key


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Devuelve la configuración cacheada del proceso."""
    return Settings()
