"""Servicio de moderación: ejecuta el pipeline, controla cuota y persiste."""

from __future__ import annotations

import hashlib

from sqlalchemy.ext.asyncio import AsyncSession

from aimoderator.config import Settings
from aimoderator.core.metrics import MODERATIONS
from aimoderator.db.models import Profile, Tenant
from aimoderator.db.repositories.moderation import create_moderation_record
from aimoderator.moderation.pipeline import ModerationDecision, ModerationPipeline
from aimoderator.schemas.common import Category
from aimoderator.schemas.moderation import ModerationRequest, ModerationResponse
from aimoderator.services.usage_service import UsageService


class ModerationService:
    """Caso de uso: moderar comentarios para un tenant y un perfil."""

    def __init__(
        self,
        pipeline: ModerationPipeline,
        settings: Settings,
        usage: UsageService | None = None,
    ) -> None:
        self._pipeline = pipeline
        self._settings = settings
        self._usage = usage or UsageService(settings)

    async def moderate(
        self,
        payload: ModerationRequest,
        *,
        session: AsyncSession,
        tenant: Tenant,
        profile: Profile | None = None,
    ) -> ModerationResponse:
        await self._usage.ensure_within_quota(session, tenant)
        response = await self._moderate_one(
            payload, session=session, tenant=tenant, profile=profile
        )
        await self._usage.consume(session, tenant)
        await session.commit()
        return response

    async def moderate_batch(
        self,
        items: list[ModerationRequest],
        *,
        session: AsyncSession,
        tenant: Tenant,
        profile: Profile | None = None,
    ) -> list[ModerationResponse]:
        await self._usage.ensure_within_quota(session, tenant, amount=len(items))
        responses = [
            await self._moderate_one(payload, session=session, tenant=tenant, profile=profile)
            for payload in items
        ]
        await self._usage.consume(session, tenant, amount=len(items))
        await session.commit()
        return responses

    async def _moderate_one(
        self,
        payload: ModerationRequest,
        *,
        session: AsyncSession,
        tenant: Tenant,
        profile: Profile | None,
    ) -> ModerationResponse:
        decision = await self._pipeline.run(
            payload.text,
            locale=payload.locale,
            platform=payload.platform,
        )
        self._record_metrics(decision)

        text_hash = hashlib.sha256(payload.text.encode("utf-8")).hexdigest()
        text_redacted: str | None = None
        if self._settings.store_redacted_text:
            text_redacted = decision.normalized_text[: self._settings.redacted_text_max_chars]

        record = await create_moderation_record(
            session,
            tenant_id=tenant.id,
            profile_id=profile.id if profile is not None else None,
            external_id=payload.external_id,
            platform=payload.platform,
            text_hash=text_hash,
            text_redacted=text_redacted,
            decision={
                "action": decision.action.value,
                "categories": decision.categories,
                "scores": decision.scores,
                "confidence": decision.confidence,
                "engine": decision.engine,
                "reasons": decision.reasons,
            },
            engine=decision.engine,
            injection_flag=decision.injection_detected,
            latency_ms=decision.latency_ms,
        )

        return ModerationResponse(
            record_id=record.id,
            action=decision.action,
            categories=[Category(value) for value in decision.categories],
            scores=decision.scores,
            confidence=decision.confidence,
            engine=decision.engine,
            injection_detected=decision.injection_detected,
            text_truncated=decision.text_truncated,
            reasons=decision.reasons,
            latency_ms=decision.latency_ms,
        )

    @staticmethod
    def _record_metrics(decision: ModerationDecision) -> None:
        MODERATIONS.labels(
            engine=decision.engine,
            action=decision.action.value,
            injection=str(decision.injection_detected).lower(),
        ).inc()
