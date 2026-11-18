"""Public endpoints for opportunities."""

import base64
import json
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.opportunity import Opportunity, OpportunityStatus
from app.schemas.opportunity import (
    FundingTypeEnum,
    OpportunityKindEnum,
    OpportunityListResponse,
    OpportunityOut,
    SortOption,
)

router = APIRouter(prefix="/opportunities", tags=["Opportunities"])


def encode_cursor(dt: datetime, item_id: uuid.UUID) -> str:
    """Encode keyset cursor as base64 string."""
    payload = {"c": dt.isoformat(), "i": str(item_id)}
    return base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8")


def decode_cursor(cursor_str: str) -> tuple[datetime, uuid.UUID]:
    """Decode keyset cursor into datetime and UUID."""
    try:
        raw = base64.urlsafe_b64decode(cursor_str.encode("utf-8")).decode("utf-8")
        data = json.loads(raw)
        dt = datetime.fromisoformat(data["c"])
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt, uuid.UUID(data["i"])
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid pagination cursor format.",
        ) from err


@router.get("", response_model=OpportunityListResponse)
async def list_opportunities(
    kind: OpportunityKindEnum | None = Query(default=None, description="Filter by opportunity kind"),
    country: str | None = Query(default=None, min_length=2, max_length=2, description="2-letter ISO country code"),
    funding: FundingTypeEnum | None = Query(default=None, description="Funding type"),
    field: str | None = Query(default=None, description="Discipline or study field"),
    deadline_min: datetime | None = Query(default=None, description="Earliest deadline (UTC)"),
    deadline_max: datetime | None = Query(default=None, description="Latest deadline (UTC)"),
    stipend_min: float | None = Query(default=None, ge=0, description="Minimum stipend amount"),
    stipend_max: float | None = Query(default=None, ge=0, description="Maximum stipend amount"),
    include_expired: bool = Query(default=False, description="Whether to include opportunities with past deadlines"),
    sort: SortOption = Query(default=SortOption.created_desc, description="Sorting criteria"),
    cursor: str | None = Query(default=None, description="Keyset pagination cursor"),
    limit: int = Query(default=20, ge=1, le=100, description="Page size limit"),
    db: AsyncSession = Depends(get_db),
) -> OpportunityListResponse:
    """Public listing of opportunities with multi-attribute filtering and keyset pagination."""
    # Base query: public users only see published items
    base_filter = [Opportunity.status == OpportunityStatus.PUBLISHED.value]

    if kind:
        base_filter.append(Opportunity.kind == kind.value)
    if country:
        base_filter.append(Opportunity.country == country.upper())
    if funding:
        base_filter.append(Opportunity.funding_type == funding.value)
    if stipend_min is not None:
        base_filter.append(
            or_(
                Opportunity.stipend_amount_min >= stipend_min,
                Opportunity.stipend_amount_max >= stipend_min,
            )
        )
    if stipend_max is not None:
        base_filter.append(
            or_(
                Opportunity.stipend_amount_min <= stipend_max,
                Opportunity.stipend_amount_max <= stipend_max,
            )
        )
    if deadline_min:
        base_filter.append(Opportunity.deadline >= deadline_min)
    if deadline_max:
        base_filter.append(Opportunity.deadline <= deadline_max)

    if not include_expired:
        now = datetime.now(UTC)
        base_filter.append(or_(Opportunity.deadline.is_(None), Opportunity.deadline >= now))

    stmt = select(Opportunity).options(selectinload(Opportunity.tags)).where(and_(*base_filter))

    if field:
        # Cross-database array/json contains check
        stmt = stmt.where(func.lower(Opportunity.fields).like(f"%{field.lower()}%"))

    # Cursor pagination handling
    if cursor:
        cursor_dt, cursor_id = decode_cursor(cursor)
        if sort == SortOption.created_desc:
            stmt = stmt.where(
                or_(
                    Opportunity.created_at < cursor_dt,
                    and_(Opportunity.created_at == cursor_dt, Opportunity.id < cursor_id),
                )
            )
        elif sort == SortOption.deadline_asc:
            stmt = stmt.where(
                or_(
                    Opportunity.deadline > cursor_dt,
                    and_(Opportunity.deadline == cursor_dt, Opportunity.id > cursor_id),
                )
            )
        elif sort == SortOption.deadline_desc:
            stmt = stmt.where(
                or_(
                    Opportunity.deadline < cursor_dt,
                    and_(Opportunity.deadline == cursor_dt, Opportunity.id < cursor_id),
                )
            )

    # Ordering
    if sort == SortOption.created_desc:
        stmt = stmt.order_by(Opportunity.created_at.desc(), Opportunity.id.desc())
    elif sort == SortOption.deadline_asc:
        stmt = stmt.order_by(Opportunity.deadline.asc().nulls_last(), Opportunity.id.asc())
    elif sort == SortOption.deadline_desc:
        stmt = stmt.order_by(Opportunity.deadline.desc().nulls_last(), Opportunity.id.desc())

    # Limit + 1 to check for next page
    stmt = stmt.limit(limit + 1)
    result = await db.execute(stmt)
    records = list(result.scalars().all())

    next_cursor = None
    if len(records) > limit:
        records = records[:limit]
        last_item = records[-1]
        if sort == SortOption.created_desc:
            next_cursor = encode_cursor(last_item.created_at, last_item.id)
        elif sort in (SortOption.deadline_asc, SortOption.deadline_desc):
            ref_dt = last_item.deadline or last_item.created_at
            next_cursor = encode_cursor(ref_dt, last_item.id)

    return OpportunityListResponse(
        items=[OpportunityOut.model_validate(r) for r in records],
        next_cursor=next_cursor,
    )


@router.get("/{opportunity_id}", response_model=OpportunityOut)
async def get_opportunity_detail(
    opportunity_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> OpportunityOut:
    """Get opportunity details by ID. Only published opportunities are returned."""
    stmt = (
        select(Opportunity)
        .options(selectinload(Opportunity.tags))
        .where(
            Opportunity.id == opportunity_id,
            Opportunity.status == OpportunityStatus.PUBLISHED.value,
        )
    )
    result = await db.execute(stmt)
    opp = result.scalar_one_or_none()

    if not opp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found or not published.",
        )

    return OpportunityOut.model_validate(opp)
