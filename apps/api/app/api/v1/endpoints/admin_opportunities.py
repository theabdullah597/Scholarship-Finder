"""Admin endpoints for opportunities CRUD, moderation, and audit logs."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import require_role
from app.db.session import get_db
from app.models.opportunity import (
    AuditLog,
    Opportunity,
    OpportunityStatus,
    Tag,
)
from app.models.user import User
from app.schemas.opportunity import (
    AuditLogOut,
    BulkModerateItemResult,
    BulkModerateRequest,
    BulkModerateResponse,
    OpportunityCreate,
    OpportunityListResponse,
    OpportunityOut,
    OpportunityPatch,
    OpportunityStatusEnum,
)

router = APIRouter(prefix="/admin", tags=["Admin Opportunities"])


async def record_audit_log(
    db: AsyncSession,
    *,
    actor_user_id: uuid.UUID,
    action: str,
    target_type: str,
    target_id: str,
    changes: dict[str, Any] | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    """Helper to record an audit log entry for admin actions."""
    audit_entry = AuditLog(
        actor_user_id=actor_user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        changes=changes,
        ip_address=ip_address,
    )
    db.add(audit_entry)
    return audit_entry


@router.get("/opportunities", response_model=OpportunityListResponse)
async def admin_list_opportunities(
    status_filter: OpportunityStatusEnum | None = Query(default=None, alias="status"),
    q: str | None = Query(default=None, description="Search keyword in title or organization"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _admin_user: User = Depends(require_role(["admin"])),
) -> OpportunityListResponse:
    """Admin view: List all opportunities with full status visibility."""
    stmt = select(Opportunity).options(selectinload(Opportunity.tags))

    if status_filter:
        stmt = stmt.where(Opportunity.status == status_filter.value)

    if q:
        search_pattern = f"%{q.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Opportunity.title).like(search_pattern),
                func.lower(Opportunity.organization).like(search_pattern),
            )
        )

    stmt = stmt.order_by(Opportunity.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    records = list(result.scalars().all())

    # Count total for admin view
    count_stmt = select(func.count(Opportunity.id))
    if status_filter:
        count_stmt = count_stmt.where(Opportunity.status == status_filter.value)
    total_count = (await db.execute(count_stmt)).scalar() or 0

    return OpportunityListResponse(
        items=[OpportunityOut.model_validate(r) for r in records],
        total_count=total_count,
    )


@router.get("/opportunities/{opportunity_id}", response_model=OpportunityOut)
async def admin_get_opportunity(
    opportunity_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin_user: User = Depends(require_role(["admin"])),
) -> OpportunityOut:
    """Admin: Get opportunity by ID regardless of status."""
    stmt = (
        select(Opportunity)
        .options(selectinload(Opportunity.tags))
        .where(Opportunity.id == opportunity_id)
    )
    result = await db.execute(stmt)
    opp = result.scalar_one_or_none()

    if not opp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found.",
        )

    return OpportunityOut.model_validate(opp)


@router.post(
    "/opportunities",
    response_model=OpportunityOut,
    status_code=status.HTTP_201_CREATED,
)
async def admin_create_opportunity(
    payload: OpportunityCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
) -> OpportunityOut:
    """Create a new opportunity with canonical URL & duplicate title+organization detection."""
    # 1. Canonical URL uniqueness check
    canonical_check = await db.execute(
        select(Opportunity).where(Opportunity.canonical_url == payload.canonical_url)
    )
    if canonical_check.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An opportunity with canonical URL '{payload.canonical_url}' already exists.",
        )

    # 2. Fuzzy duplicate title + organization check
    fuzzy_check = await db.execute(
        select(Opportunity).where(
            func.lower(Opportunity.title) == payload.title.lower().strip(),
            func.lower(Opportunity.organization) == payload.organization.lower().strip(),
        )
    )
    if fuzzy_check.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Duplicate opportunity detected with title '{payload.title}' and organization '{payload.organization}'.",
        )

    opp = Opportunity(
        kind=payload.kind.value,
        title=payload.title.strip(),
        organization=payload.organization.strip(),
        description=payload.description.strip(),
        country=payload.country.upper().strip(),
        fields=payload.fields,
        funding_type=payload.funding_type.value,
        stipend_amount_min=payload.stipend_amount_min,
        stipend_amount_max=payload.stipend_amount_max,
        stipend_currency=payload.stipend_currency.upper() if payload.stipend_currency else None,
        deadline=payload.deadline,
        source_url=payload.source_url.strip(),
        canonical_url=payload.canonical_url.strip(),
        status=OpportunityStatus.PENDING_REVIEW.value,
    )

    if payload.tag_ids:
        tag_query = await db.execute(select(Tag).where(Tag.id.in_(payload.tag_ids)))
        opp.tags = list(tag_query.scalars().all())

    db.add(opp)
    await db.flush()

    # Record Audit Log
    ip_addr = request.client.host if request.client else None
    await record_audit_log(
        db,
        actor_user_id=current_user.id,
        action="opportunity.create",
        target_type="opportunity",
        target_id=str(opp.id),
        changes={
            "title": opp.title,
            "organization": opp.organization,
            "canonical_url": opp.canonical_url,
            "status": opp.status,
        },
        ip_address=ip_addr,
    )

    await db.commit()

    # Reload with relationships
    stmt = (
        select(Opportunity)
        .options(selectinload(Opportunity.tags))
        .where(Opportunity.id == opp.id)
    )
    opp = (await db.execute(stmt)).scalar_one()

    return OpportunityOut.model_validate(opp)


@router.patch("/opportunities/{opportunity_id}", response_model=OpportunityOut)
async def admin_patch_opportunity(
    opportunity_id: uuid.UUID,
    payload: OpportunityPatch,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
) -> OpportunityOut:
    """Patch/update an opportunity and write an audit log row with diff."""
    stmt = (
        select(Opportunity)
        .options(selectinload(Opportunity.tags))
        .where(Opportunity.id == opportunity_id)
    )
    result = await db.execute(stmt)
    opp = result.scalar_one_or_none()

    if not opp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found.",
        )

    # Check canonical URL conflict if changed
    if payload.canonical_url and payload.canonical_url != opp.canonical_url:
        canon_dup = await db.execute(
            select(Opportunity).where(
                Opportunity.canonical_url == payload.canonical_url,
                Opportunity.id != opportunity_id,
            )
        )
        if canon_dup.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Another opportunity already uses canonical URL '{payload.canonical_url}'.",
            )

    changes: dict[str, Any] = {}
    data = payload.model_dump(exclude_unset=True)
    tag_ids = data.pop("tag_ids", None)

    for field, new_val in data.items():
        old_val = getattr(opp, field)
        if field in ("kind", "funding_type", "status") and new_val is not None:
            new_val_str = new_val.value if hasattr(new_val, "value") else str(new_val)
            if old_val != new_val_str:
                changes[field] = {"old": str(old_val), "new": new_val_str}
                setattr(opp, field, new_val_str)
        elif field == "country" and new_val is not None:
            new_country = new_val.upper()
            if old_val != new_country:
                changes[field] = {"old": str(old_val), "new": new_country}
                setattr(opp, field, new_country)
        else:
            if old_val != new_val:
                changes[field] = {"old": str(old_val), "new": str(new_val)}
                setattr(opp, field, new_val)

    if tag_ids is not None:
        tag_query = await db.execute(select(Tag).where(Tag.id.in_(tag_ids)))
        opp.tags = list(tag_query.scalars().all())
        changes["tags"] = {"new_tag_count": len(opp.tags)}

    if changes:
        ip_addr = request.client.host if request.client else None
        await record_audit_log(
            db,
            actor_user_id=current_user.id,
            action="opportunity.patch",
            target_type="opportunity",
            target_id=str(opportunity_id),
            changes=changes,
            ip_address=ip_addr,
        )

    await db.commit()

    # Reload with relationships
    stmt = (
        select(Opportunity)
        .options(selectinload(Opportunity.tags))
        .where(Opportunity.id == opportunity_id)
    )
    opp = (await db.execute(stmt)).scalar_one()

    return OpportunityOut.model_validate(opp)


@router.post("/opportunities/{opportunity_id}/verify", response_model=OpportunityOut)
async def admin_verify_opportunity(
    opportunity_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
) -> OpportunityOut:
    """Verify and publish an opportunity (transitions status to 'published')."""
    stmt = (
        select(Opportunity)
        .options(selectinload(Opportunity.tags))
        .where(Opportunity.id == opportunity_id)
    )
    result = await db.execute(stmt)
    opp = result.scalar_one_or_none()

    if not opp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found.",
        )

    old_status = opp.status
    opp.status = OpportunityStatus.PUBLISHED.value

    ip_addr = request.client.host if request.client else None
    await record_audit_log(
        db,
        actor_user_id=current_user.id,
        action="opportunity.verify",
        target_type="opportunity",
        target_id=str(opportunity_id),
        changes={"status": {"old": old_status, "new": opp.status}},
        ip_address=ip_addr,
    )

    await db.commit()

    # Reload with relationships
    stmt = (
        select(Opportunity)
        .options(selectinload(Opportunity.tags))
        .where(Opportunity.id == opportunity_id)
    )
    opp = (await db.execute(stmt)).scalar_one()
    return OpportunityOut.model_validate(opp)


@router.post("/opportunities/{opportunity_id}/archive", response_model=OpportunityOut)
async def admin_archive_opportunity(
    opportunity_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
) -> OpportunityOut:
    """Archive an opportunity (transitions status to 'archived')."""
    stmt = (
        select(Opportunity)
        .options(selectinload(Opportunity.tags))
        .where(Opportunity.id == opportunity_id)
    )
    result = await db.execute(stmt)
    opp = result.scalar_one_or_none()

    if not opp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found.",
        )

    old_status = opp.status
    opp.status = OpportunityStatus.ARCHIVED.value

    ip_addr = request.client.host if request.client else None
    await record_audit_log(
        db,
        actor_user_id=current_user.id,
        action="opportunity.archive",
        target_type="opportunity",
        target_id=str(opportunity_id),
        changes={"status": {"old": old_status, "new": opp.status}},
        ip_address=ip_addr,
    )

    await db.commit()

    # Reload with relationships
    stmt = (
        select(Opportunity)
        .options(selectinload(Opportunity.tags))
        .where(Opportunity.id == opportunity_id)
    )
    opp = (await db.execute(stmt)).scalar_one()
    return OpportunityOut.model_validate(opp)


@router.post("/opportunities/bulk-moderate", response_model=BulkModerateResponse)
async def admin_bulk_moderate(
    payload: BulkModerateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
) -> BulkModerateResponse:
    """Bulk approve/publish, reject, or archive opportunities with audit logging."""
    results: list[BulkModerateItemResult] = []
    ip_addr = request.client.host if request.client else None

    action_to_status = {
        "approve": OpportunityStatus.PUBLISHED.value,
        "publish": OpportunityStatus.PUBLISHED.value,
        "reject": OpportunityStatus.REJECTED.value,
        "archive": OpportunityStatus.ARCHIVED.value,
    }

    for item in payload.items:
        stmt = select(Opportunity).where(Opportunity.id == item.id)
        opp = (await db.execute(stmt)).scalar_one_or_none()

        if not opp:
            results.append(
                BulkModerateItemResult(
                    id=item.id,
                    action=item.action.value,
                    success=False,
                    error="Opportunity not found.",
                )
            )
            continue

        target_status = action_to_status.get(item.action.value, opp.status)
        old_status = opp.status
        opp.status = target_status

        await record_audit_log(
            db,
            actor_user_id=current_user.id,
            action=f"opportunity.bulk_{item.action.value}",
            target_type="opportunity",
            target_id=str(opp.id),
            changes={"status": {"old": old_status, "new": target_status}},
            ip_address=ip_addr,
        )

        results.append(
            BulkModerateItemResult(
                id=item.id,
                action=item.action.value,
                success=True,
                status=target_status,
            )
        )

    await db.commit()
    return BulkModerateResponse(processed=len(results), results=results)


@router.get("/audit-logs", response_model=list[AuditLogOut])
async def admin_list_audit_logs(
    target_type: str | None = Query(default=None),
    target_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _admin_user: User = Depends(require_role(["admin"])),
) -> list[AuditLogOut]:
    """Retrieve system audit logs for administrative tracking."""
    stmt = select(AuditLog)
    if target_type:
        stmt = stmt.where(AuditLog.target_type == target_type)
    if target_id:
        stmt = stmt.where(AuditLog.target_id == target_id)

    stmt = stmt.order_by(AuditLog.created_at.desc()).limit(limit)
    logs = list((await db.execute(stmt)).scalars().all())
    return [AuditLogOut.model_validate(log_entry) for log_entry in logs]
