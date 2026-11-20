"""Schemas for administrative user management and analytics."""

import enum
import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class AdminRoleEnum(enum.StrEnum):
    student = "student"
    admin = "admin"


class AdminUserOut(BaseModel):
    id: uuid.UUID
    email: str
    role: str
    is_verified: bool
    is_suspended: bool
    created_at: datetime


class AdminUserUpdate(BaseModel):
    role: AdminRoleEnum | None = None
    is_suspended: bool | None = None


class BroadcastRequest(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    message: str = Field(min_length=2, max_length=5000)
    audience: AdminRoleEnum | None = None


class BroadcastResponse(BaseModel):
    recipients: int
    notification_kind: str


class AdminAnalytics(BaseModel):
    users_total: int
    users_students: int
    users_admins: int
    users_suspended: int
    opportunities_published: int
    opportunities_pending: int
    applications_total: int
    ingestion_runs_total: int
