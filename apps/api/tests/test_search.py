"""Focused tests for grounded hybrid search and resilience controls."""

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.opportunity import Opportunity, OpportunityStatus
from app.services.ai_provider import LLMProvider
from app.services.search import search_opportunities


class FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self.values.get(key)

    async def set(self, key: str, value: str, ex: int) -> bool:
        self.values[key] = value
        return True


class RankingProvider(LLMProvider):
    async def complete_json(self, prompt: str) -> dict[str, Any]:
        return {
            "ranking": [
                {"id": "missing", "score": 999, "reason": "<b>ignore</b>"},
                {"id": "valid", "score": 0.75, "reason": "<b>Strong match</b>"},
            ]
        }

    async def embed(self, text: str) -> list[float]:
        return [1.0]


class BrokenProvider(LLMProvider):
    async def complete_json(self, prompt: str) -> dict[str, Any]:
        raise RuntimeError("provider unavailable")

    async def embed(self, text: str) -> list[float]:
        raise RuntimeError("provider unavailable")


@pytest.mark.asyncio
async def test_search_only_returns_published_and_validates_provider_ids(db_session: AsyncSession) -> None:
    published = Opportunity(
        kind="scholarship",
        title="AI Research Scholarship",
        organization="Berlin Institute",
        description="Fully funded artificial intelligence research.",
        country="DE",
        fields=["Computer Science"],
        funding_type="fully_funded",
        source_url="https://example.org/ai",
        canonical_url="https://example.org/ai",
        status=OpportunityStatus.PUBLISHED.value,
        deadline=datetime.now(UTC) + timedelta(days=30),
    )
    hidden = Opportunity(
        kind="scholarship",
        title="Hidden AI Scholarship",
        organization="Private Institute",
        description="Not published.",
        country="US",
        fields=["Computer Science"],
        funding_type="fully_funded",
        source_url="https://example.org/hidden",
        canonical_url="https://example.org/hidden",
        status=OpportunityStatus.PENDING_REVIEW.value,
    )
    db_session.add_all([published, hidden])
    await db_session.commit()
    published_id = str(published.id)

    class Provider(RankingProvider):
        async def complete_json(self, prompt: str) -> dict[str, Any]:
            return {
                "ranking": [
                    {"id": "unknown", "score": 5, "reason": "<b>bad</b>"},
                    {"id": published_id, "score": 5, "reason": "<b>Strong match</b>"},
                ]
            }

    results, cached, fallback = await search_opportunities(
        db_session,
        FakeRedis(),
        user_id="user-1",
        query="AI scholarship",
        provider=Provider(),
    )

    assert cached is False
    assert fallback is False
    assert len(results) == 1
    assert results[0].opportunity.id == published.id
    assert results[0].score == 1
    assert results[0].reason == "Strong match"


@pytest.mark.asyncio
async def test_search_fallback_and_cache(db_session: AsyncSession) -> None:
    opportunity = Opportunity(
        kind="fellowship",
        title="Climate Research Fellowship",
        organization="Green Lab",
        description="Research funding for climate science.",
        country="SE",
        fields=["Climate Science"],
        funding_type="partially_funded",
        source_url="https://example.org/climate",
        canonical_url="https://example.org/climate",
        status=OpportunityStatus.PUBLISHED.value,
    )
    db_session.add(opportunity)
    await db_session.commit()
    redis = FakeRedis()

    first, first_cached, fallback = await search_opportunities(
        db_session,
        redis,
        user_id="user-2",
        query="climate",
        provider=BrokenProvider(),
    )
    second, second_cached, second_fallback = await search_opportunities(
        db_session,
        redis,
        user_id="user-2",
        query="climate",
        provider=BrokenProvider(),
    )

    assert first and first_cached is False and fallback is True
    assert second and second_cached is True and second_fallback is True
    assert second[0].opportunity.id == first[0].opportunity.id
