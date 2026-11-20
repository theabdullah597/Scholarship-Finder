"""Schemas for grounded AI opportunity search."""

from pydantic import BaseModel, Field

from app.schemas.opportunity import OpportunityOut


class SearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=500)


class SearchResult(BaseModel):
    opportunity: OpportunityOut
    score: float = Field(ge=0, le=1)
    reason: str = Field(max_length=300)


class SearchResponse(BaseModel):
    results: list[SearchResult]
    cached: bool
    fallback: bool
    remaining_requests: int | None = None
