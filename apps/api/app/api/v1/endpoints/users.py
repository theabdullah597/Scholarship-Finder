from datetime import UTC, datetime

import sqlalchemy as sa
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_active_user
from app.db.session import get_db
from app.models.student import Application, Note, Notification
from app.models.user import RefreshToken, StudentProfile, User
from app.schemas.auth import StudentProfileUpdate, UserResponse

router = APIRouter()


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current authenticated user profile",
)
async def get_me(
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update current student profile",
)
async def update_me(
    data: StudentProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    profile = current_user.profile
    if not profile:
        profile = StudentProfile(user_id=current_user.id)
        db.add(profile)
        current_user.profile = profile

    if data.full_name is not None:
        profile.full_name = data.full_name
    if data.citizenship is not None:
        profile.citizenship = data.citizenship.upper() if data.citizenship else None
    if data.target_countries is not None:
        profile.target_countries = [c.upper() for c in data.target_countries]
    if data.fields_of_interest is not None:
        profile.fields_of_interest = data.fields_of_interest
    if data.target_degree_level is not None:
        profile.target_degree_level = data.target_degree_level
    if data.timezone is not None:
        profile.timezone = data.timezone

    await db.commit()

    # Re-fetch user with loaded profile for serialization
    stmt = (
        select(User)
        .where(User.id == current_user.id)
        .options(selectinload(User.profile))
    )
    result = await db.execute(stmt)
    updated_user = result.scalar_one()

    return UserResponse.model_validate(updated_user)


@router.get("/me/export")
async def export_my_data(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Export the authenticated user's data without exposing other users' records."""
    applications = list(
        (
            await db.execute(select(Application).where(Application.user_id == current_user.id))
        ).scalars().all()
    )
    notes = list((await db.execute(select(Note).where(Note.user_id == current_user.id))).scalars().all())
    notifications = list(
        (await db.execute(select(Notification).where(Notification.user_id == current_user.id))).scalars().all()
    )
    payload = {
        "user": {
            "id": str(current_user.id),
            "email": current_user.email,
            "role": current_user.role.value,
            "created_at": current_user.created_at.isoformat(),
        },
        "profile": UserResponse.model_validate(current_user).model_dump(mode="json").get("profile"),
        "applications": [
            {
                "id": str(item.id),
                "opportunity_id": str(item.opportunity_id),
                "status": item.status,
                "applied_at": item.applied_at.isoformat() if item.applied_at else None,
                "created_at": item.created_at.isoformat(),
            }
            for item in applications
        ],
        "notes": [
            {
                "id": str(item.id),
                "opportunity_id": str(item.opportunity_id),
                "content": item.content,
                "created_at": item.created_at.isoformat(),
                "updated_at": item.updated_at.isoformat(),
            }
            for item in notes
        ],
        "notifications": [
            {
                "id": str(item.id),
                "kind": item.kind,
                "title": item.title,
                "message": item.message,
                "read_at": item.read_at.isoformat() if item.read_at else None,
                "created_at": item.created_at.isoformat(),
            }
            for item in notifications
        ],
    }
    return JSONResponse(content=payload)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_account(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Soft-delete the account and revoke all refresh tokens immediately."""
    current_user.deleted_at = datetime.now(UTC)
    await db.execute(
        sa.update(RefreshToken)
        .where(RefreshToken.user_id == current_user.id)
        .values(is_revoked=True)
    )
    await db.commit()
