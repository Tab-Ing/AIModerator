"""Repositorio de bitácora de auditoría."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from aimoderator.db.models import AuditLog


async def create_audit_log(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID | None,
    actor: str | None,
    action: str,
    payload: dict[str, Any],
) -> AuditLog:
    entry = AuditLog(tenant_id=tenant_id, actor=actor, action=action, payload=payload)
    session.add(entry)
    await session.flush()
    return entry
