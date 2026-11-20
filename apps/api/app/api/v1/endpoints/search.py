"""Authenticated grounded AI search endpoint."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.redis import get_redis_client
from app.schemas.opportunity import OpportunityOut
from app.schemas.search import SearchRequest, SearchResponse, SearchResult
from app.services.search import search_opportunities

logger = logging.getLogger("opportunityabroad.search.api")
router = APIRouter(prefix="/search", tags=["AI Search"])


@router.post("", response_model=SearchResponse)
async def search(
    payload: SearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SearchResponse:
    redis = await get_redis_client()
    rate_key = f"search-rate:{current_user.id}"
    remaining: int | None = None
    try:
        count = int(await redis.incr(rate_key))
        if count == 1:
            await redis.expire(rate_key, 3600)
        remaining = max(0, 30 - count)
        if count > 30:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Search rate limit exceeded. Try again later.",
            )
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Search rate limiter unavailable: %s", exc)

    results, cached, fallback = await search_opportunities(
        db,
        redis,
        user_id=str(current_user.id),
        query=payload.query,
    )
    return SearchResponse(
        results=[
            SearchResult(
                opportunity=OpportunityOut.model_validate(result.opportunity),
                score=result.score,
                reason=result.reason,
            )
            for result in results
        ],
        cached=cached,
        fallback=fallback,
        remaining_requests=remaining,
    )
