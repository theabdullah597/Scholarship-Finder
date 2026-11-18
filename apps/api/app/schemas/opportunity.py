"""Pydantic v2 schemas for opportunities, sources, tags, and audit logs."""

import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# ---------- Enums ----------


class OpportunityKindEnum(enum.StrEnum):
    scholarship = "scholarship"
    internship = "internship"
    fellowship = "fellowship"
    grant = "grant"


class FundingTypeEnum(enum.StrEnum):
    fully_funded = "fully_funded"
    partially_funded = "partially_funded"
    unfunded = "unfunded"
    other = "other"


class OpportunityStatusEnum(enum.StrEnum):
    pending_review = "pending_review"
    published = "published"
    archived = "archived"
    rejected = "rejected"


class SortOption(enum.StrEnum):
    created_desc = "created_desc"
    deadline_asc = "deadline_asc"
    deadline_desc = "deadline_desc"


# ---------- Tag ----------


class TagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    category: str | None = None


class TagCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    category: str | None = Field(default=None, max_length=64)


# ---------- Source ----------


class SourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    source_type: str
    url: str
    config: dict[str, Any] = Field(default_factory=dict)
    is_active: bool
    fetch_interval_minutes: int
    last_run_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class SourceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    source_type: str = Field(pattern="^(rss|json_api|html_scraper)$")
    url: str
    config: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    fetch_interval_minutes: int = 720


# ---------- Opportunity ----------


class OpportunityCreate(BaseModel):
    kind: OpportunityKindEnum
    title: str = Field(min_length=2, max_length=512)
    organization: str = Field(min_length=2, max_length=255)
    description: str = Field(min_length=10)
    country: str = Field(min_length=2, max_length=2)
    fields: list[str] = Field(default_factory=list)
    funding_type: FundingTypeEnum
    stipend_amount_min: Decimal | None = None
    stipend_amount_max: Decimal | None = None
    stipend_currency: str | None = Field(default=None, min_length=3, max_length=3)
    deadline: datetime | None = None
    source_url: str = Field(min_length=5)
    canonical_url: str = Field(min_length=5)
    tag_ids: list[uuid.UUID] = Field(default_factory=list)


class OpportunityPatch(BaseModel):
    kind: OpportunityKindEnum | None = None
    title: str | None = Field(default=None, min_length=2, max_length=512)
    organization: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = Field(default=None, min_length=10)
    country: str | None = Field(default=None, min_length=2, max_length=2)
    fields: list[str] | None = None
    funding_type: FundingTypeEnum | None = None
    stipend_amount_min: Decimal | None = None
    stipend_amount_max: Decimal | None = None
    stipend_currency: str | None = Field(default=None, min_length=3, max_length=3)
    deadline: datetime | None = None
    source_url: str | None = Field(default=None, min_length=5)
    canonical_url: str | None = Field(default=None, min_length=5)
    status: OpportunityStatusEnum | None = None
    tag_ids: list[uuid.UUID] | None = None


class OpportunityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_id: uuid.UUID | None = None
    kind: str
    title: str
    organization: str
    description: str
    country: str
    fields: list[str]
    funding_type: str
    stipend_amount_min: Decimal | None = None
    stipend_amount_max: Decimal | None = None
    stipend_currency: str | None = None
    deadline: datetime | None = None
    source_url: str
    canonical_url: str
    status: str
    tags: list[TagOut] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class OpportunityListResponse(BaseModel):
    items: list[OpportunityOut]
    next_cursor: str | None = None
    total_count: int | None = None


# ---------- Bulk Moderation ----------


class BulkModerateAction(enum.StrEnum):
    approve = "approve"  # transitions to published
    publish = "publish"
    reject = "reject"
    archive = "archive"


class BulkModerateItem(BaseModel):
    id: uuid.UUID
    action: BulkModerateAction


class BulkModerateRequest(BaseModel):
    items: list[BulkModerateItem] = Field(min_length=1, max_length=100)


class BulkModerateItemResult(BaseModel):
    id: uuid.UUID
    action: str
    success: bool
    status: str | None = None
    error: str | None = None


class BulkModerateResponse(BaseModel):
    processed: int
    results: list[BulkModerateItemResult]


# ---------- Audit Log ----------


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    actor_user_id: uuid.UUID | None = None
    action: str
    target_type: str
    target_id: str
    changes: dict[str, Any] | None = None
    ip_address: str | None = None
    created_at: datetime
