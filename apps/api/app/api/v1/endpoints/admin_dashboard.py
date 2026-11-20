"""Administrative user management, analytics, broadcasts, and audit views."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_role
from app.api.v1.endpoints.admin_opportunities import record_audit_log
from app.db.session import get_db
from app.models.ingestion import IngestionRun
from app.models.opportunity import Opportunity, OpportunityStatus
from app.models.student import Application, Notification
from app.models.user import User, UserRole
from app.schemas.admin import (
    AdminAnalytics,
    AdminRoleEnum,
    AdminUserOut,
    AdminUserUpdate,
    BroadcastRequest,
    BroadcastResponse,
)

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])


def mask_email(email: str) -> str:
    """Mask the local part while retaining enough information for admin recognition."""
    local, separator, domain = email.partition("@")
    if not separator:
        return "***"
    visible = local[:2] if len(local) > 2 else local[:1]
    return f"{visible}***@{domain}"


def user_out(user: User) -> AdminUserOut:
    return AdminUserOut(
        id=user.id,
        email=mask_email(user.email),
        role=user.role.value,
        is_verified=user.is_verified,
        is_suspended=user.is_suspended,
        created_at=user.created_at,
    )


@router.get("/users", response_model=list[AdminUserOut])
async def list_users(
    q: str | None = Query(default=None, max_length=255),
    role: AdminRoleEnum | None = None,
    suspended: bool | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_role(["admin"])),
) -> list[AdminUserOut]:
    stmt = select(User).where(User.deleted_at.is_(None))
    if q:
        stmt = stmt.where(func.lower(User.email).like(f"%{q.lower()}%"))
    if role:
        stmt = stmt.where(User.role == role.value)
    if suspended is not None:
        stmt = stmt.where(User.is_suspended.is_(suspended))
    users = list((await db.execute(stmt.order_by(User.created_at.desc()).offset(offset).limit(limit))).scalars().all())
    return [user_out(user) for user in users]


@router.patch("/users/{user_id}", response_model=AdminUserOut)
async def update_user(
    user_id: uuid.UUID,
    payload: AdminUserUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(require_role(["admin"])),
) -> AdminUserOut:
    user = (
        await db.execute(select(User).where(User.id == user_id, User.deleted_at.is_(None)))
    ).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    if user.id == current_admin.id and payload.is_suspended is True:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot suspend your own account.")

    changes: dict[str, Any] = {}
    if payload.role is not None and user.role.value != payload.role.value:
        changes["role"] = {"from": user.role.value, "to": payload.role.value}
        user.role = UserRole(payload.role.value)
    if payload.is_suspended is not None and user.is_suspended != payload.is_suspended:
        changes["is_suspended"] = {"from": user.is_suspended, "to": payload.is_suspended}
        user.is_suspended = payload.is_suspended
    if changes:
        await record_audit_log(
            db,
            actor_user_id=current_admin.id,
            action="user.update",
            target_type="user",
            target_id=str(user.id),
            changes=changes,
            ip_address=request.client.host if request.client else None,
        )
    await db.commit()
    await db.refresh(user)
    return user_out(user)


@router.get("/analytics", response_model=AdminAnalytics)
async def analytics(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_role(["admin"])),
) -> AdminAnalytics:
    users_total = (await db.execute(select(func.count(User.id)).where(User.deleted_at.is_(None)))).scalar() or 0
    users_students = (
        await db.execute(select(func.count(User.id)).where(User.deleted_at.is_(None), User.role == UserRole.STUDENT.value))
    ).scalar() or 0
    users_admins = (
        await db.execute(select(func.count(User.id)).where(User.deleted_at.is_(None), User.role == UserRole.ADMIN.value))
    ).scalar() or 0
    users_suspended = (
        await db.execute(select(func.count(User.id)).where(User.deleted_at.is_(None), User.is_suspended.is_(True)))
    ).scalar() or 0
    published = (
        await db.execute(select(func.count(Opportunity.id)).where(Opportunity.status == OpportunityStatus.PUBLISHED.value))
    ).scalar() or 0
    pending = (
        await db.execute(select(func.count(Opportunity.id)).where(Opportunity.status == OpportunityStatus.PENDING_REVIEW.value))
    ).scalar() or 0
    applications = (await db.execute(select(func.count(Application.id)))).scalar() or 0
    runs = (await db.execute(select(func.count(IngestionRun.id)))).scalar() or 0
    return AdminAnalytics(
        users_total=users_total,
        users_students=users_students,
        users_admins=users_admins,
        users_suspended=users_suspended,
        opportunities_published=published,
        opportunities_pending=pending,
        applications_total=applications,
        ingestion_runs_total=runs,
    )


@router.post("/broadcasts", response_model=BroadcastResponse, status_code=status.HTTP_201_CREATED)
async def broadcast(
    payload: BroadcastRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(require_role(["admin"])),
) -> BroadcastResponse:
    stmt = select(User).where(User.deleted_at.is_(None), User.is_suspended.is_(False))
    if payload.audience:
        stmt = stmt.where(User.role == payload.audience.value)
    recipients = list((await db.execute(stmt)).scalars().all())
    broadcast_id = uuid.uuid4()
    for user in recipients:
        db.add(
            Notification(
                user_id=user.id,
                kind="admin_broadcast",
                title=payload.title,
                message=payload.message,
                dedupe_key=f"broadcast:{broadcast_id}:{user.id}",
            )
        )
    await record_audit_log(
        db,
        actor_user_id=current_admin.id,
        action="notification.broadcast",
        target_type="notification",
        target_id=str(broadcast_id),
        changes={"audience": payload.audience.value if payload.audience else "all", "recipients": len(recipients)},
        ip_address=request.client.host if request.client else None,
    )
    await db.commit()
    return BroadcastResponse(recipients=len(recipients), notification_kind="admin_broadcast")


