"""init schema

Revision ID: 0001_init
Revises:
Create Date: 2026-09-29
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_init"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("plan", sa.String(length=30), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("settings", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tenants_slug"), "tenants", ["slug"], unique=True)

    op.create_table(
        "api_keys",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("key_hash", sa.String(length=128), nullable=False),
        sa.Column("prefix", sa.String(length=16), nullable=False),
        sa.Column("label", sa.String(length=100), nullable=True),
        sa.Column("scopes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_api_keys_tenant_id"), "api_keys", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_api_keys_key_hash"), "api_keys", ["key_hash"], unique=True)

    op.create_table(
        "profiles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("engine_config", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("policy_rules", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "name", name="uq_profiles_tenant_name"),
    )
    op.create_index(op.f("ix_profiles_tenant_id"), "profiles", ["tenant_id"], unique=False)

    op.create_table(
        "moderation_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("profile_id", sa.Uuid(), nullable=True),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("platform", sa.String(length=50), nullable=True),
        sa.Column("text_hash", sa.String(length=64), nullable=False),
        sa.Column("text_redacted", sa.Text(), nullable=True),
        sa.Column("decision", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("engine", sa.String(length=50), nullable=True),
        sa.Column("injection_flag", sa.Boolean(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_moderation_records_tenant_id"), "moderation_records", ["tenant_id"], unique=False
    )
    op.create_index(
        op.f("ix_moderation_records_profile_id"), "moderation_records", ["profile_id"], unique=False
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=True),
        sa.Column("actor", sa.String(length=100), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_logs_tenant_id"), "audit_logs", ["tenant_id"], unique=False)

    op.create_table(
        "usage_counters",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("period", sa.String(length=20), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "period", name="uq_usage_tenant_period"),
    )
    op.create_index(
        op.f("ix_usage_counters_tenant_id"), "usage_counters", ["tenant_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_usage_counters_tenant_id"), table_name="usage_counters")
    op.drop_table("usage_counters")
    op.drop_index(op.f("ix_audit_logs_tenant_id"), table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index(op.f("ix_moderation_records_profile_id"), table_name="moderation_records")
    op.drop_index(op.f("ix_moderation_records_tenant_id"), table_name="moderation_records")
    op.drop_table("moderation_records")
    op.drop_index(op.f("ix_profiles_tenant_id"), table_name="profiles")
    op.drop_table("profiles")
    op.drop_index(op.f("ix_api_keys_key_hash"), table_name="api_keys")
    op.drop_index(op.f("ix_api_keys_tenant_id"), table_name="api_keys")
    op.drop_table("api_keys")
    op.drop_index(op.f("ix_tenants_slug"), table_name="tenants")
    op.drop_table("tenants")
