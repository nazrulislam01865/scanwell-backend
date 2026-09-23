"""create admin auth tables

Revision ID: 20260922_0004
Revises: 20260919_0003
Create Date: 2026-09-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260922_0004"
down_revision: str | None = "20260919_0003"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "auth_admins",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=80), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="Active",
        ),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_auth_admins_email"),
    )
    op.create_index("ix_auth_admins_email", "auth_admins", ["email"], unique=False)

    op.create_table(
        "admin_auth_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("admin_id", sa.Uuid(), nullable=False),
        sa.Column("refresh_token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_reason", sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(["admin_id"], ["auth_admins.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "refresh_token_hash",
            name="uq_admin_auth_sessions_refresh_token_hash",
        ),
    )
    op.create_index(
        "ix_admin_auth_sessions_admin_id",
        "admin_auth_sessions",
        ["admin_id"],
        unique=False,
    )
    op.create_index(
        "ix_admin_auth_sessions_admin_active",
        "admin_auth_sessions",
        ["admin_id", "revoked_at"],
        unique=False,
    )
    op.create_index(
        "ix_admin_auth_sessions_expires_at",
        "admin_auth_sessions",
        ["expires_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_admin_auth_sessions_expires_at", table_name="admin_auth_sessions")
    op.drop_index("ix_admin_auth_sessions_admin_active", table_name="admin_auth_sessions")
    op.drop_index("ix_admin_auth_sessions_admin_id", table_name="admin_auth_sessions")
    op.drop_table("admin_auth_sessions")
    op.drop_index("ix_auth_admins_email", table_name="auth_admins")
    op.drop_table("auth_admins")
