import enum
import uuid
from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class UserRole(enum.StrEnum):
    STUDENT = "student"
    ADMIN = "admin"


# Transparent array for PostgreSQL with JSON fallback for SQLite
StringListType = sa.ARRAY(sa.String).with_variant(sa.JSON, "sqlite")


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(
        sa.String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    password_hash: Mapped[str] = mapped_column(
        sa.String(255),
        nullable=False,
    )
    role: Mapped[UserRole] = mapped_column(
        sa.Enum(UserRole, native_enum=False, values_callable=lambda x: [e.value for e in x]),
        default=UserRole.STUDENT,
        nullable=False,
    )
    is_verified: Mapped[bool] = mapped_column(
        sa.Boolean,
        default=False,
        nullable=False,
    )
    verification_token: Mapped[str | None] = mapped_column(
        sa.String(255),
        nullable=True,
        index=True,
    )
    reset_password_token: Mapped[str | None] = mapped_column(
        sa.String(255),
        nullable=True,
        index=True,
    )
    reset_password_expires_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=True,
    )
    is_suspended: Mapped[bool] = mapped_column(
        sa.Boolean,
        default=False,
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    profile: Mapped[Optional["StudentProfile"]] = relationship(
        "StudentProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class StudentProfile(Base, TimestampMixin):
    __tablename__ = "student_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    full_name: Mapped[str | None] = mapped_column(
        sa.String(255),
        nullable=True,
    )
    citizenship: Mapped[str | None] = mapped_column(
        sa.String(2),
        nullable=True,
    )
    target_countries: Mapped[list[str]] = mapped_column(
        StringListType,
        default=list,
        nullable=False,
    )
    fields_of_interest: Mapped[list[str]] = mapped_column(
        StringListType,
        default=list,
        nullable=False,
    )
    target_degree_level: Mapped[str | None] = mapped_column(
        sa.String(50),
        nullable=True,
    )
    timezone: Mapped[str] = mapped_column(
        sa.String(64),
        default="UTC",
        nullable=False,
    )

    user: Mapped["User"] = relationship("User", back_populates="profile")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    family_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid(as_uuid=True),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(
        sa.String(255),
        unique=True,
        index=True,
        nullable=False,
    )
    is_revoked: Mapped[bool] = mapped_column(
        sa.Boolean,
        default=False,
        nullable=False,
    )
    expires_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )
    user_agent: Mapped[str | None] = mapped_column(
        sa.String(512),
        nullable=True,
    )
    ip_address: Mapped[str | None] = mapped_column(
        sa.String(64),
        nullable=True,
    )

    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")
