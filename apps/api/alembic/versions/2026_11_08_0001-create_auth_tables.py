"""create auth tables

Revision ID: 2026_11_08_0001
Revises:
Create Date: 2026-11-08 11:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "2026_11_08_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=32), server_default="student", nullable=False),
        sa.Column("is_verified", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("verification_token", sa.String(length=255), nullable=True),
        sa.Column("reset_password_token", sa.String(length=255), nullable=True),
        sa.Column("reset_password_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_suspended", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
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
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_verification_token", "users", ["verification_token"])
    op.create_index("ix_users_reset_password_token", "users", ["reset_password_token"])

    # Create student_profiles table
    op.create_table(
        "student_profiles",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("citizenship", sa.String(length=2), nullable=True),
        sa.Column(
            "target_countries",
            sa.ARRAY(sa.String()).with_variant(sa.JSON(), "sqlite"),
            nullable=False,
        ),
        sa.Column(
            "fields_of_interest",
            sa.ARRAY(sa.String()).with_variant(sa.JSON(), "sqlite"),
            nullable=False,
        ),
        sa.Column("target_degree_level", sa.String(length=50), nullable=True),
        sa.Column("timezone", sa.String(length=64), server_default="UTC", nullable=False),
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
    )
    op.create_index("ix_student_profiles_user_id", "student_profiles", ["user_id"], unique=True)

    # Create refresh_tokens table
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("family_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("is_revoked", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
    )
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=True)
    op.create_index("ix_refresh_tokens_family_id", "refresh_tokens", ["family_id"])
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])


def downgrade() -> None:
    op.drop_table("refresh_tokens")
    op.drop_table("student_profiles")
    op.drop_table("users")
