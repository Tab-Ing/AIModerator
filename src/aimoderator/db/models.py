"""Modelos de datos (PostgreSQL)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from aimoderator.db.base import Base


class Tenant(Base):
    """Empresa que consume la API con su propia configuración."""

    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    plan: Mapped[str] = mapped_column(String(30), nullable=False, default="free")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    settings: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    api_keys: Mapped[list[ApiKey]] = relationship(
        "ApiKey", back_populates="tenant", cascade="all, delete-orphan"
    )
    profiles: Mapped[list[Profile]] = relationship(
        "Profile", back_populates="tenant", cascade="all, delete-orphan"
    )


class ApiKey(Base):
    """Credencial de acceso de un tenant. Se guarda solo el hash."""

    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    key_hash: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    prefix: Mapped[str] = mapped_column(String(16), nullable=False)
    label: Mapped[str | None] = mapped_column(String(100))
    scopes: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    tenant: Mapped[Tenant] = relationship("Tenant", back_populates="api_keys")


class Profile(Base):
    """Perfil de uso: política de bloqueo + modelo/motor a utilizar."""

    __tablename__ = "profiles"
    __table_args__ = (UniqueConstraint("tenant_id", "name", name="uq_profiles_tenant_name"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    engine_config: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    policy_rules: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    tenant: Mapped[Tenant] = relationship("Tenant", back_populates="profiles")


class ModerationRecord(Base):
    """Registro de una decisión de moderación (texto hasheado/redactado)."""

    __tablename__ = "moderation_records"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    profile_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("profiles.id", ondelete="SET NULL"), index=True
    )
    external_id: Mapped[str | None] = mapped_column(String(255))
    platform: Mapped[str | None] = mapped_column(String(50))
    text_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    text_redacted: Mapped[str | None] = mapped_column(Text)
    decision: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    engine: Mapped[str | None] = mapped_column(String(50))
    injection_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class AuditLog(Base):
    """Bitácora de acciones relevantes por tenant."""

    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    actor: Mapped[str | None] = mapped_column(String(100))
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class UsageCounter(Base):
    """Contador de uso por tenant y período (cuotas por plan)."""

    __tablename__ = "usage_counters"
    __table_args__ = (UniqueConstraint("tenant_id", "period", name="uq_usage_tenant_period"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    period: Mapped[str] = mapped_column(String(20), nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
