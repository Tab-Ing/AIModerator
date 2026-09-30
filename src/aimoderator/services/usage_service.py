"""Servicio de uso y cuotas diarias."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from aimoderator.config import Settings
from aimoderator.core.errors import QuotaExceededError
from aimoderator.db.models import Tenant
from aimoderator.db.repositories import usage as usage_repo
from aimoderator.schemas.common import Plan
from aimoderator.schemas.usage import UsageRead


def current_period(now: datetime | None = None) -> str:
    """Período diario en formato ``YYYY-MM-DD``."""
    moment = now or datetime.now(UTC)
    return moment.date().isoformat()


class UsageService:
    """Controla el consumo diario de moderaciones por tenant."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def quota_for(self, tenant: Tenant) -> int:
        if tenant.plan == Plan.COMMERCIAL.value:
            return self._settings.commercial_plan_daily_quota
        return self._settings.free_plan_daily_quota

    async def current_usage(self, session: AsyncSession, tenant: Tenant) -> UsageRead:
        period = current_period()
        used = await usage_repo.get_count(session, tenant.id, period)
        quota = self.quota_for(tenant)
        plan = tenant.plan if tenant.plan in set(Plan) else Plan.FREE.value
        return UsageRead(
            plan=Plan(plan),
            period=period,
            used=used,
            quota=quota,
            remaining=max(0, quota - used),
        )

    async def ensure_within_quota(
        self, session: AsyncSession, tenant: Tenant, amount: int = 1
    ) -> None:
        period = current_period()
        used = await usage_repo.get_count(session, tenant.id, period)
        if used + amount > self.quota_for(tenant):
            raise QuotaExceededError("Cuota diaria de moderación excedida")

    async def consume(self, session: AsyncSession, tenant: Tenant, amount: int = 1) -> None:
        await usage_repo.increment_count(session, tenant.id, current_period(), amount)
