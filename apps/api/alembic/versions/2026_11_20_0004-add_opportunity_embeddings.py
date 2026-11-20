"""add opportunity embeddings

Revision ID: 2026_11_20_0004
Revises: 2026_11_08_0003
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "2026_11_20_0004"
down_revision: str | None = "2026_11_08_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("opportunities", sa.Column("embedding", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("opportunities", "embedding")
