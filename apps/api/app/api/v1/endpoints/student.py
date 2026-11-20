"""Student-owned applications, notes, and notifications."""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user
from app.db.session import get_db
from app.models.opportunity import Opportunity, OpportunityStatus
from app.models.student import Application, ApplicationStatus, Note, Notification
from app.models.user import User
from app.schemas.opportunity import OpportunityOut
from app.schemas.student import (
    ApplicationCreate,
    ApplicationOut,
    ApplicationUpdate,
    NoteCreate,
    NoteOut,
    NoteUpdate,
    NotificationOut,
)

router = APIRouter(prefix="/student", tags=["Student Dashboard"])


async def _application_out(db: AsyncSession, application: Application) -> ApplicationOut:
    opportunity = (
        await db.execute(select(Opportunity).where(Opportunity.id == application.opportunity_id))
    ).scalar_one()
    return ApplicationOut(
        id=application.id,
        opportunity=OpportunityOut.model_validate(opportunity),
        status=application.status,
        applied_at=application.applied_at,
        created_at=application.created_at,
        updated_at=application.updated_at,
    )


@router.get("/applications", response_model=list[ApplicationOut])
async def list_applications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[ApplicationOut]:
    applications = list(
        (
            await db.execute(
                select(Application)
                .where(Application.user_id == current_user.id)
                .order_by(Application.updated_at.desc())
            )
        ).scalars().all()
    )
    return [await _application_out(db, application) for application in applications]


@router.post("/applications", response_model=ApplicationOut, status_code=status.HTTP_201_CREATED)
async def save_application(
    payload: ApplicationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ApplicationOut:
    opportunity = (
        await db.execute(
            select(Opportunity).where(
                Opportunity.id == payload.opportunity_id,
                Opportunity.status == OpportunityStatus.PUBLISHED.value,
            )
        )
    ).scalar_one_or_none()
    if not opportunity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found or not published.")

    application = (
        await db.execute(
            select(Application).where(
                Application.user_id == current_user.id,
                Application.opportunity_id == payload.opportunity_id,
            )
        )
    ).scalar_one_or_none()
    if application:
        return await _application_out(db, application)

    application = Application(user_id=current_user.id, opportunity_id=payload.opportunity_id)
    db.add(application)
    await db.commit()
    await db.refresh(application)
    return ApplicationOut(
        id=application.id,
        opportunity=OpportunityOut.model_validate(opportunity),
        status=application.status,
        applied_at=application.applied_at,
        created_at=application.created_at,
        updated_at=application.updated_at,
    )


@router.patch("/applications/{application_id}", response_model=ApplicationOut)
async def update_application(
    application_id: uuid.UUID,
    payload: ApplicationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ApplicationOut:
    application = (
        await db.execute(
            select(Application).where(Application.id == application_id, Application.user_id == current_user.id)
        )
    ).scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")
    application.status = payload.status.value
    if payload.status in {
        ApplicationStatus.SUBMITTED,
        ApplicationStatus.INTERVIEWING,
        ApplicationStatus.ACCEPTED,
    } and application.applied_at is None:
        application.applied_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(application)
    return await _application_out(db, application)


@router.delete("/applications/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(
    application_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    application = (
        await db.execute(
            select(Application).where(Application.id == application_id, Application.user_id == current_user.id)
        )
    ).scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found.")
    await db.delete(application)
    await db.commit()


@router.get("/notes", response_model=list[NoteOut])
async def list_notes(
    opportunity_id: uuid.UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[NoteOut]:
    stmt = select(Note).where(Note.user_id == current_user.id).order_by(Note.updated_at.desc())
    if opportunity_id:
        stmt = stmt.where(Note.opportunity_id == opportunity_id)
    return [NoteOut.model_validate(note) for note in (await db.execute(stmt)).scalars().all()]


@router.post("/notes", response_model=NoteOut, status_code=status.HTTP_201_CREATED)
async def create_note(
    payload: NoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> NoteOut:
    opportunity = (await db.execute(select(Opportunity).where(Opportunity.id == payload.opportunity_id))).scalar_one_or_none()
    if not opportunity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found.")
    note = Note(user_id=current_user.id, opportunity_id=payload.opportunity_id, content=payload.content.strip())
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return NoteOut.model_validate(note)


@router.patch("/notes/{note_id}", response_model=NoteOut)
async def update_note(
    note_id: uuid.UUID,
    payload: NoteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> NoteOut:
    note = (
        await db.execute(select(Note).where(Note.id == note_id, Note.user_id == current_user.id))
    ).scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found.")
    note.content = payload.content.strip()
    await db.commit()
    await db.refresh(note)
    return NoteOut.model_validate(note)


@router.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    note_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    note = (
        await db.execute(select(Note).where(Note.id == note_id, Note.user_id == current_user.id))
    ).scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found.")
    await db.delete(note)
    await db.commit()


@router.get("/notifications", response_model=list[NotificationOut])
async def list_notifications(
    unread_only: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[NotificationOut]:
    stmt = select(Notification).where(Notification.user_id == current_user.id).order_by(Notification.created_at.desc()).limit(100)
    if unread_only:
        stmt = stmt.where(Notification.read_at.is_(None))
    return [
        NotificationOut.model_validate(notification)
        for notification in (await db.execute(stmt)).scalars().all()
    ]


@router.post("/notifications/{notification_id}/read", response_model=NotificationOut)
async def mark_notification_read(
    notification_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> NotificationOut:
    notification = (
        await db.execute(
            select(Notification).where(Notification.id == notification_id, Notification.user_id == current_user.id)
        )
    ).scalar_one_or_none()
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    notification.read_at = notification.read_at or datetime.now(UTC)
    await db.commit()
    await db.refresh(notification)
    return NotificationOut.model_validate(notification)
