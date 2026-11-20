"""Deduplication engine: canonical URL matching followed by fuzzy title + organization matching."""

import re
from difflib import SequenceMatcher
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.opportunity import Opportunity, OpportunityStatus, Source


def _normalize_string_for_fuzzy(text: str) -> str:
    """Normalize string by removing punctuation, converting to lowercase, and collapsing spaces."""
    cleaned = re.sub(r"[^\w\s]", "", text.lower())
    return re.sub(r"\s+", " ", cleaned).strip()


def _is_fuzzy_duplicate(left: str, right: str, *, threshold: float = 0.92) -> bool:
    """Return whether two normalized values are close enough to represent the same value."""
    return SequenceMatcher(
        None,
        _normalize_string_for_fuzzy(left),
        _normalize_string_for_fuzzy(right),
    ).ratio() >= threshold


async def find_existing_opportunity(
    db: AsyncSession,
    *,
    canonical_url: str,
    title: str,
    organization: str,
) -> Opportunity | None:
    """Search for existing opportunity: First by exact canonical URL, then by fuzzy (title, organization)."""
    # 1. Primary check: Canonical URL
    canon_stmt = select(Opportunity).where(Opportunity.canonical_url == canonical_url)
    res_canon = await db.execute(canon_stmt)
    existing = res_canon.scalar_one_or_none()
    if existing:
        return existing

    # 2. Secondary check: fuzzy title + organization. Restrict candidates by organization
    # prefix so this remains bounded without requiring database-specific trigram support.
    norm_org = _normalize_string_for_fuzzy(organization)
    fuzzy_stmt = select(Opportunity).where(
        func.lower(Opportunity.organization).like(f"{norm_org[:12]}%")
    ).limit(100)
    candidates = (await db.execute(fuzzy_stmt)).scalars().all()
    for candidate in candidates:
        if _is_fuzzy_duplicate(candidate.title, title) and _is_fuzzy_duplicate(
            candidate.organization,
            organization,
        ):
            return candidate

    return None


async def ingest_or_update_opportunity(
    db: AsyncSession,
    *,
    source: Source,
    normalized_data: dict[str, Any],
) -> tuple[Opportunity, bool]:
    """Insert new opportunity or update existing record without producing duplicates.

    Returns (Opportunity, is_created: bool).
    """
    canonical_url = normalized_data["canonical_url"]
    title = normalized_data["title"]
    organization = normalized_data["organization"]

    existing = await find_existing_opportunity(
        db,
        canonical_url=canonical_url,
        title=title,
        organization=organization,
    )

    if existing:
        # Update mutable fields (deadline, stipend, description if changed)
        if normalized_data.get("deadline"):
            existing.deadline = normalized_data["deadline"]
        if normalized_data.get("stipend_amount_min") is not None:
            existing.stipend_amount_min = normalized_data["stipend_amount_min"]
        if normalized_data.get("stipend_amount_max") is not None:
            existing.stipend_amount_max = normalized_data["stipend_amount_max"]
        if normalized_data.get("description") and len(normalized_data["description"]) > len(existing.description):
            existing.description = normalized_data["description"]

        existing.source_id = source.id
        return existing, False

    # Create new opportunity (pending review by default for moderation queue)
    new_opp = Opportunity(
        source_id=source.id,
        kind=normalized_data["kind"],
        title=title,
        organization=organization,
        description=normalized_data["description"],
        country=normalized_data["country"],
        fields=normalized_data["fields"],
        funding_type=normalized_data["funding_type"],
        stipend_amount_min=normalized_data.get("stipend_amount_min"),
        stipend_amount_max=normalized_data.get("stipend_amount_max"),
        stipend_currency=normalized_data.get("stipend_currency"),
        deadline=normalized_data.get("deadline"),
        source_url=normalized_data["source_url"],
        canonical_url=canonical_url,
        status=OpportunityStatus.PENDING_REVIEW.value,
    )
    db.add(new_opp)
    return new_opp, True
