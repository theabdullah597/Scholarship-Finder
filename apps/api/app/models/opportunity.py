"""Opportunity-related models: Source, Opportunity, Tag, OpportunityTag, AuditLog."""

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

# Compatible JSON and Array types for SQLite tests & Postgres prod
JSONType = postgresql.JSONB().with_variant(sa.JSON(), "sqlite")
StringListType = sa.ARRAY(sa.String).with_variant(sa.JSON(), "sqlite")


# ---------- Enums ----------


class OpportunityKind(enum.StrEnum):
    SCHOLARSHIP = "scholarship"
    INTERNSHIP = "internship"
    FELLOWSHIP = "fellowship"
    GRANT = "grant"


class FundingType(enum.StrEnum):
    FULLY_FUNDED = "fully_funded"
    PARTIALLY_FUNDED = "partially_funded"
    UNFUNDED = "unfunded"
    OTHER = "other"


class OpportunityStatus(enum.StrEnum):
    PENDING_REVIEW = "pending_review"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    REJECTED = "rejected"


# ---------- Source ----------


class Source(Base, TimestampMixin):
    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(sa.String(32), nullable=False)  # rss, json_api, html_scraper
    url: Mapped[str] = mapped_column(sa.Text, nullable=False)
    config: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict, nullable=False)
    is_active: Mapped[bool] = mapped_column(sa.Boolean, default=True, nullable=False)
    fetch_interval_minutes: Mapped[int] = mapped_column(sa.Integer, default=720, nullable=False)
    last_run_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)

    opportunities: Mapped[list["Opportunity"]] = relationship(
        "Opportunity",
        back_populates="source",
        cascade="all, delete-orphan",
    )


# ---------- Tag ----------


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(sa.String(64), unique=True, index=True, nullable=False)
    category: Mapped[str | None] = mapped_column(sa.String(64), nullable=True)


# ---------- OpportunityTag (association table) ----------


class OpportunityTag(Base):
    __tablename__ = "opportunity_tags"

    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("opportunities.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    )


# ---------- Opportunity ----------


class Opportunity(Base, TimestampMixin):
    __tablename__ = "opportunities"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("sources.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    kind: Mapped[str] = mapped_column(sa.String(32), nullable=False, index=True)
    title: Mapped[str] = mapped_column(sa.String(512), nullable=False, index=True)
    organization: Mapped[str] = mapped_column(sa.String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(sa.Text, nullable=False)
    country: Mapped[str] = mapped_column(sa.String(2), nullable=False, index=True)  # ISO 3166-1 alpha-2
    fields: Mapped[list[str]] = mapped_column(StringListType, default=list, nullable=False)
    funding_type: Mapped[str] = mapped_column(sa.String(32), nullable=False, index=True)
    stipend_amount_min: Mapped[Decimal | None] = mapped_column(sa.Numeric(12, 2), nullable=True)
    stipend_amount_max: Mapped[Decimal | None] = mapped_column(sa.Numeric(12, 2), nullable=True)
    stipend_currency: Mapped[str | None] = mapped_column(sa.String(3), nullable=True)  # ISO 4217
    deadline: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True, index=True)
    source_url: Mapped[str] = mapped_column(sa.Text, nullable=False)
    canonical_url: Mapped[str] = mapped_column(sa.Text, unique=True, index=True, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(JSONType, nullable=True)
    status: Mapped[str] = mapped_column(
        sa.String(32),
        default=OpportunityStatus.PENDING_REVIEW.value,
        nullable=False,
        index=True,
    )

    source: Mapped[Source | None] = relationship("Source", back_populates="opportunities")
    tags: Mapped[list[Tag]] = relationship(
        "Tag",
        secondary="opportunity_tags",
        lazy="selectin",
    )

    __table_args__ = (
        sa.Index("ix_opportunities_status_deadline", "status", "deadline"),
        sa.Index("ix_opportunities_status_created_at", "status", "created_at"),
        sa.Index("ix_opportunities_country_funding", "country", "funding_type"),
    )


# ---------- AuditLog ----------


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action: Mapped[str] = mapped_column(sa.String(128), nullable=False, index=True)
    target_type: Mapped[str] = mapped_column(sa.String(64), nullable=False, index=True)
    target_id: Mapped[str] = mapped_column(sa.String(64), nullable=False, index=True)
    changes: Mapped[dict[str, Any] | None] = mapped_column(JSONType, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(sa.String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
        index=True,
    )
