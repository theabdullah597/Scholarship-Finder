"""Grounded hybrid opportunity search with resilience controls."""

import hashlib
import json
import logging
import re
import time
import uuid
from dataclasses import dataclass
from typing import Any

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.opportunity import Opportunity, OpportunityStatus
from app.services.ai_provider import LLMProvider, deterministic_embedding, get_llm_provider

logger = logging.getLogger("opportunityabroad.search")


@dataclass
class RankedOpportunity:
    opportunity: Opportunity
    score: float
    reason: str


class ProviderCircuit:
    """Small in-process circuit breaker shared by search requests."""

    def __init__(self) -> None:
        self.failures = 0
        self.open_until = 0.0

    def available(self) -> bool:
        return time.monotonic() >= self.open_until

    def success(self) -> None:
        self.failures = 0
        self.open_until = 0.0

    def failure(self) -> None:
        self.failures += 1
        if self.failures >= 3:
            self.open_until = time.monotonic() + 60


circuit = ProviderCircuit()


def _clean_reason(value: Any) -> str:
    text = re.sub(r"<[^>]*>", "", str(value or ""))
    return re.sub(r"\s+", " ", text).strip()[:300]


def _lexical_score(query: str, opportunity: Opportunity) -> float:
    query_tokens = set(re.findall(r"\w+", query.lower()))
    text = " ".join(
        [opportunity.title, opportunity.organization, opportunity.description, *opportunity.fields]
    ).lower()
    if not query_tokens:
        return 0.0
    return min(1.0, sum(token in text for token in query_tokens) / len(query_tokens))


def _cosine(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = sum(value * value for value in left) ** 0.5
    right_norm = sum(value * value for value in right) ** 0.5
    return dot / (left_norm * right_norm) if left_norm and right_norm else 0.0


async def _cached(redis: Redis, key: str) -> dict[str, Any] | None:
    try:
        value = await redis.get(key)
        return json.loads(value) if value else None
    except Exception as exc:
        logger.warning("Search cache unavailable: %s", exc)
        return None


async def _cache(redis: Redis, key: str, value: dict[str, Any]) -> None:
    try:
        await redis.set(key, json.dumps(value), ex=600)
    except Exception as exc:
        logger.warning("Search cache write unavailable: %s", exc)


async def search_opportunities(
    db: AsyncSession,
    redis: Redis,
    *,
    user_id: str,
    query: str,
    provider: LLMProvider | None = None,
) -> tuple[list[RankedOpportunity], bool, bool]:
    """Search only published opportunities and return (results, cached, fallback)."""
    cache_key = "search:" + hashlib.sha256(f"{user_id}:{query.strip().lower()}".encode()).hexdigest()
    cached = await _cached(redis, cache_key)
    if cached:
        cached_ids = [str(item.get("id")) for item in cached.get("results", []) if isinstance(item, dict)]
        if cached_ids:
            records = list(
                (
                    await db.execute(
                        select(Opportunity).where(
                            Opportunity.id.in_([uuid.UUID(item_id) for item_id in cached_ids]),
                            Opportunity.status == OpportunityStatus.PUBLISHED.value,
                        )
                    )
                ).scalars().all()
            )
            by_id = {str(record.id): record for record in records}
            restored = [
                RankedOpportunity(
                    opportunity=by_id[item["id"]],
                    score=float(item["score"]),
                    reason=_clean_reason(item["reason"]),
                )
                for item in cached["results"]
                if item["id"] in by_id
            ]
            return restored, True, bool(cached.get("fallback", False))

    records = list((await db.execute(
        select(Opportunity).where(Opportunity.status == OpportunityStatus.PUBLISHED.value)
    )).scalars().all())
    active_provider = provider or get_llm_provider()
    fallback = True
    query_embedding = deterministic_embedding(query)
    provider_embedding: list[float] | None = None
    if circuit.available():
        try:
            provider_embedding = await active_provider.embed(query)
        except Exception as exc:
            circuit.failure()
            logger.warning("AI embedding provider failed; using deterministic embedding: %s", exc)
    if provider_embedding:
        query_embedding = provider_embedding
    scored: list[tuple[Opportunity, float]] = []
    for opportunity in records:
        semantic = _cosine(query_embedding, opportunity.embedding or deterministic_embedding(opportunity.title))
        lexical = _lexical_score(query, opportunity)
        scored.append((opportunity, 0.6 * semantic + 0.4 * lexical))
    scored.sort(key=lambda item: item[1], reverse=True)
    candidates = scored[:50]

    ranking: dict[str, dict[str, Any]] = {}
    if circuit.available():
        try:
            candidate_payload = [
                {"id": str(item.id), "title": item.title, "organization": item.organization}
                for item, _score in candidates
            ]
            response = await active_provider.complete_json(
                json.dumps({"query": query, "candidates": candidate_payload})
            )
            raw_ranking = response.get("ranking", [])
            if isinstance(raw_ranking, list):
                valid_ids = {str(item.id) for item, _score in candidates}
                for item in raw_ranking:
                    if not isinstance(item, dict) or str(item.get("id")) not in valid_ids:
                        continue
                    try:
                        score = max(0.0, min(1.0, float(item.get("score", 0))))
                    except (TypeError, ValueError):
                        continue
                    ranking[str(item["id"])] = {
                        "score": score,
                        "reason": _clean_reason(item.get("reason")) or "Matches your search.",
                    }
            if ranking:
                fallback = False
            circuit.success()
        except Exception as exc:
            circuit.failure()
            logger.warning("AI search provider failed; using fallback: %s", exc)

    results = [
        RankedOpportunity(
            opportunity=item,
            score=ranking.get(str(item.id), {}).get("score", score),
            reason=ranking.get(str(item.id), {}).get("reason", "Matches your keywords and opportunity profile."),
        )
        for item, score in candidates
    ]
    results.sort(key=lambda item: item.score, reverse=True)
    await _cache(
        redis,
        cache_key,
        {
            "fallback": fallback,
            "results": [
                {"id": str(result.opportunity.id), "score": result.score, "reason": result.reason}
                for result in results[:20]
            ],
        },
    )
    return results[:20], False, fallback
