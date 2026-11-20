"""Pydantic schemas for sources and ingestion runs."""

import enum
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class IngestionStatusEnum(enum.StrEnum):
    running = "running"
    success = "success"
    partial_failure = "partial_failure"
    failed = "failed"


class SourceTypeEnum(enum.StrEnum):
    rss = "rss"
    json_api = "json_api"
    html_scraper = "html_scraper"


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
    name: str = Field(min_length=2, max_length=255)
    source_type: SourceTypeEnum
    url: str = Field(min_length=5)
    config: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    fetch_interval_minutes: int = Field(default=720, ge=15, le=10080)


class SourceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    source_type: SourceTypeEnum | None = None
    url: str | None = Field(default=None, min_length=5)
    config: dict[str, Any] | None = None
    is_active: bool | None = None
    fetch_interval_minutes: int | None = Field(default=None, ge=15, le=10080)


class IngestionRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_id: uuid.UUID
    status: str
    items_found: int
    items_created: int
    items_updated: int
    items_failed: int
    error_log: str | None = None
    started_at: datetime
    finished_at: datetime | None = None
    source_name: str | None = None


class RunNowResponse(BaseModel):
    message: str
    run_id: uuid.UUID
    source_id: uuid.UUID
    status: str
    items_found: int
    items_created: int
    items_updated: int
    items_failed: int

