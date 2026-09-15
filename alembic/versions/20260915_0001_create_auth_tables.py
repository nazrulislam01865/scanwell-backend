"""create auth users and verification codes

Revision ID: 20260915_0001
Revises:
Create Date: 2026-09-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260915_0001"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "auth_users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("phone", sa.String(length=40), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("preferred_login_method", sa.String(length=20), nullable=False),
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_auth_users_email"),
    )
    op.create_index("ix_auth_users_email", "auth_users", ["email"], unique=False)

    op.create_table(
        "auth_verification_codes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("purpose", sa.String(length=32), nullable=False),
        sa.Column("code_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["auth_users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_auth_verification_codes_user_id",
        "auth_verification_codes",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_auth_verification_codes_lookup",
        "auth_verification_codes",
        ["user_id", "purpose", "consumed_at", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_auth_verification_codes_lookup", table_name="auth_verification_codes")
    op.drop_index("ix_auth_verification_codes_user_id", table_name="auth_verification_codes")
    op.drop_table("auth_verification_codes")
    op.drop_index("ix_auth_users_email", table_name="auth_users")
    op.drop_table("auth_users")
