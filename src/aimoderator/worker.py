"""Worker de arq: procesa lotes de moderación en segundo plano."""

from __future__ import annotations

import uuid
from typing import Any

import httpx
from arq.connections import RedisSettings
from arq.typing import WorkerSettingsBase
from arq.worker import run_worker

from aimoderator.config import get_settings
from aimoderator.db.repositories.profile import get_profile
from aimoderator.db.repositories.tenant import get_tenant
from aimoderator.db.session import SessionLocal
from aimoderator.moderation.pipeline import build_pipeline
from aimoderator.schemas.moderation import ModerationRequest
from aimoderator.services.moderation_service import ModerationService


async def moderate_batch_task(
    ctx: dict[str, Any],
    tenant_id: str,
    profile_id: str | None,
    items: list[dict[str, Any]],
) -> dict[str, Any]:
    """Modera un lote para un tenant/perfil y devuelve los resultados serializados."""
    settings = get_settings()
    async with SessionLocal() as session:
        tenant = await get_tenant(session, uuid.UUID(tenant_id))
        if tenant is None:
            raise ValueError("Tenant inexistente")

        profile = (
            await get_profile(session, tenant.id, uuid.UUID(profile_id))
            if profile_id is not None
            else None
        )

        client = httpx.AsyncClient()
        try:
            pipeline = build_pipeline(
                settings,
                client,
                engine_config=profile.engine_config if profile else None,
                policy_rules=profile.policy_rules if profile else None,
            )
            service = ModerationService(pipeline, settings)
            payloads = [ModerationRequest.model_validate(item) for item in items]
            results = await service.moderate_batch(
                payloads, session=session, tenant=tenant, profile=profile
            )
        finally:
            await client.aclose()

    return {
        "count": len(results),
        "results": [result.model_dump(mode="json") for result in results],
    }


class WorkerSettings(WorkerSettingsBase):
    """Configuración del worker de arq (``python -m aimoderator.worker``)."""

    functions = [moderate_batch_task]
    redis_settings: RedisSettings = RedisSettings.from_dsn(get_settings().redis_url)
    max_jobs = 10
    job_timeout = 120


def run() -> None:
    """Levanta el worker (bloqueante): ``python -m aimoderator.worker``."""
    run_worker(WorkerSettings)


if __name__ == "__main__":
    run()
