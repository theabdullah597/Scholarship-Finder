"""Admin endpoints for managing ingestion sources, triggering run-now, and viewing run history."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import require_role
from app.db.session import get_db
from app.models.ingestion import IngestionRun
from app.models.opportunity import AuditLog, Source
from app.models.user import User
from app.schemas.ingestion import (
    IngestionRunOut,
    RunNowResponse,
    SourceCreate,
    SourceOut,
    SourceUpdate,
)
from app.services.ingestion.engine import IngestionEngine

router = APIRouter(prefix="/admin", tags=["Admin Sources & Ingestion"])


async def record_source_audit(
    db: AsyncSession,
    *,
    actor_user_id: uuid.UUID,
    action: str,
    target_id: str,
    changes: dict[str, Any] | None = None,
) -> None:
    """Record an auditable source-management action without storing request PII."""
    db.add(
        AuditLog(
            actor_user_id=actor_user_id,
            action=action,
            target_type="source",
            target_id=target_id,
            changes=changes,
        )
    )


@router.get("/sources", response_model=list[SourceOut])
async def list_admin_sources(
    db: AsyncSession = Depends(get_db),
    _admin_user: User = Depends(require_role(["admin"])),
) -> list[SourceOut]:
    """List all configured opportunity ingestion sources."""
    stmt = select(Source).order_by(Source.created_at.desc())
    sources = list((await db.execute(stmt)).scalars().all())
    return [SourceOut.model_validate(s) for s in sources]


@router.post("/sources", response_model=SourceOut, status_code=status.HTTP_201_CREATED)
async def create_admin_source(
    payload: SourceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
) -> SourceOut:
    """Create a new opportunity ingestion source."""
    # Check duplicate source URL
    existing = (
        await db.execute(select(Source).where(Source.url == payload.url.strip()))
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Source with URL '{payload.url}' already exists.",
        )

    new_source = Source(
        name=payload.name.strip(),
        source_type=payload.source_type.value,
        url=payload.url.strip(),
        config=payload.config,
        is_active=payload.is_active,
        fetch_interval_minutes=payload.fetch_interval_minutes,
    )
    db.add(new_source)
    await db.flush()
    await record_source_audit(
        db,
        actor_user_id=current_user.id,
        action="source.create",
        target_id=str(new_source.id),
        changes={"name": new_source.name, "source_type": new_source.source_type},
    )
    await db.commit()
    await db.refresh(new_source)
    return SourceOut.model_validate(new_source)


@router.patch("/sources/{source_id}", response_model=SourceOut)
async def update_admin_source(
    source_id: uuid.UUID,
    payload: SourceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
) -> SourceOut:
    """Update source parameters such as fetch interval, config, or active status."""
    stmt = select(Source).where(Source.id == source_id)
    source = (await db.execute(stmt)).scalar_one_or_none()

    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found.",
        )

    data = payload.model_dump(exclude_unset=True)
    if "url" in data and data["url"] is not None:
        duplicate = (
            await db.execute(
                select(Source).where(Source.url == data["url"].strip(), Source.id != source_id)
            )
        ).scalar_one_or_none()
        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Source with URL '{data['url']}' already exists.",
            )
        data["url"] = data["url"].strip()
    changes: dict[str, Any] = {}
    for field, val in data.items():
        if field == "source_type" and val is not None:
            changes[field] = {"from": source.source_type, "to": val.value}
            source.source_type = val.value if hasattr(val, "value") else str(val)
        elif val is not None:
            changes[field] = {"from": getattr(source, field), "to": val}
            setattr(source, field, val)

    await record_source_audit(
        db,
        actor_user_id=current_user.id,
        action="source.patch",
        target_id=str(source.id),
        changes=changes,
    )
    await db.commit()
    await db.refresh(source)
    return SourceOut.model_validate(source)


@router.post("/sources/{source_id}/run-now", response_model=RunNowResponse)
async def trigger_source_run_now(
    source_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
) -> RunNowResponse:
    """Trigger an immediate ingestion run for a specific source."""
    stmt = select(Source).where(Source.id == source_id)
    source = (await db.execute(stmt)).scalar_one_or_none()

    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found.",
        )

    # Execute ingestion synchronously in API request context
    run = await IngestionEngine.run_ingestion_for_source(db, source)
    await record_source_audit(
        db,
        actor_user_id=current_user.id,
        action="source.run_now",
        target_id=str(source.id),
        changes={"run_id": str(run.id), "status": run.status},
    )
    await db.commit()

    return RunNowResponse(
        message=f"Ingestion run completed with status '{run.status}'.",
        run_id=run.id,
        source_id=source.id,
        status=run.status,
        items_found=run.items_found,
        items_created=run.items_created,
        items_updated=run.items_updated,
        items_failed=run.items_failed,
    )


@router.get("/ingestion-runs", response_model=list[IngestionRunOut])
async def list_ingestion_runs(
    source_id: uuid.UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _admin_user: User = Depends(require_role(["admin"])),
) -> list[IngestionRunOut]:
    """View ingestion run history with created, updated, and failure counts."""
    stmt = select(IngestionRun).options(selectinload(IngestionRun.source))
    if source_id:
        stmt = stmt.where(IngestionRun.source_id == source_id)

    stmt = stmt.order_by(IngestionRun.started_at.desc()).limit(limit)
    runs = list((await db.execute(stmt)).scalars().all())

    results: list[IngestionRunOut] = []
    for r in runs:
        item = IngestionRunOut.model_validate(r)
        if r.source:
            item.source_name = r.source.name
        results.append(item)

    return results
