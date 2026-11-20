"""Ingestion models: IngestionRun and related statuses."""

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.opportunity import Source


class IngestionStatus(enum.StrEnum):
    RUNNING = "running"
    SUCCESS = "success"
    PARTIAL_FAILURE = "partial_failure"
    FAILED = "failed"


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        sa.String(32),
        default=IngestionStatus.RUNNING.value,
        nullable=False,
        index=True,
    )
    items_found: Mapped[int] = mapped_column(sa.Integer, default=0, nullable=False)
    items_created: Mapped[int] = mapped_column(sa.Integer, default=0, nullable=False)
    items_updated: Mapped[int] = mapped_column(sa.Integer, default=0, nullable=False)
    items_failed: Mapped[int] = mapped_column(sa.Integer, default=0, nullable=False)
    error_log: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
        index=True,
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    source: Mapped["Source"] = relationship("Source", lazy="joined")  # noqa: F821

