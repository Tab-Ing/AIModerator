"""Esquemas de uso y cuotas."""

from __future__ import annotations

from aimoderator.schemas.common import APIModel, Plan


class UsageRead(APIModel):
    """Consumo diario y cuota del tenant."""

    plan: Plan
    period: str
    used: int
    quota: int
    remaining: int
