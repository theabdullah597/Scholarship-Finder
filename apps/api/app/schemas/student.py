"""Schemas for student-owned data."""

import enum
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.opportunity import OpportunityOut


class ApplicationStatusEnum(enum.StrEnum):
    saved = "saved"
    in_progress = "in_progress"
    submitted = "submitted"
    interviewing = "interviewing"
    accepted = "accepted"
    rejected = "rejected"
    withdrawn = "withdrawn"


class ApplicationCreate(BaseModel):
    opportunity_id: uuid.UUID


class ApplicationUpdate(BaseModel):
    status: ApplicationStatusEnum


class ApplicationOut(BaseModel):
    id: uuid.UUID
    opportunity: OpportunityOut
    status: str
    applied_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class NoteCreate(BaseModel):
    opportunity_id: uuid.UUID
    content: str = Field(min_length=1, max_length=10000)


class NoteUpdate(BaseModel):
    content: str = Field(min_length=1, max_length=10000)


class NoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    opportunity_id: uuid.UUID
    content: str
    created_at: datetime
    updated_at: datetime


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    kind: str
    title: str
    message: str
    read_at: datetime | None = None
    created_at: datetime
