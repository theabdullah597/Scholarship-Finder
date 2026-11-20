"""Provider abstractions for grounded AI search."""

import hashlib
from abc import ABC, abstractmethod
from typing import Any

import httpx

from app.config import settings


class LLMProvider(ABC):
    """Interface for structured completion and embedding providers."""

    @abstractmethod
    async def complete_json(self, prompt: str) -> dict[str, Any]:
        """Return a structured JSON object for a trusted application prompt."""

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Return an embedding for text."""


class FakeProvider(LLMProvider):
    """Deterministic provider used locally and in tests."""

    async def complete_json(self, prompt: str) -> dict[str, Any]:
        import json

        payload = json.loads(prompt)
        query = str(payload.get("query", "")).lower()
        ranking = []
        for candidate in payload.get("candidates", []):
            title = str(candidate.get("title", "")).lower()
            organization = str(candidate.get("organization", "")).lower()
            score = 0.8 if any(token in f"{title} {organization}" for token in query.split()) else 0.4
            ranking.append(
                {
                    "id": candidate.get("id"),
                    "score": score,
                    "reason": "Matches the requested opportunity keywords.",
                }
            )
        return {"ranking": ranking}

    async def embed(self, text: str) -> list[float]:
        return deterministic_embedding(text)


class OpenAIProvider(LLMProvider):
    """OpenAI-compatible provider loaded only when explicitly configured."""

    async def _request(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not settings.AI_API_KEY:
            raise RuntimeError("AI_API_KEY is not configured")
        headers = {"Authorization": f"Bearer {settings.AI_API_KEY}"}
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                f"{settings.AI_BASE_URL.rstrip('/')}/{endpoint}",
                headers=headers,
                json=payload,
            )
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise RuntimeError("AI provider returned an invalid response")
        return data

    async def complete_json(self, prompt: str) -> dict[str, Any]:
        data = await self._request(
            "chat/completions",
            {
                "model": settings.AI_MODEL,
                "temperature": 0,
                "response_format": {"type": "json_object"},
                "messages": [
                    {
                        "role": "system",
                        "content": "Return JSON only. Use only opportunity IDs supplied by the application.",
                    },
                    {"role": "user", "content": prompt},
                ],
            },
        )
        content = data["choices"][0]["message"]["content"]
        import json

        result = json.loads(content)
        if not isinstance(result, dict):
            raise RuntimeError("AI provider returned non-object JSON")
        return result

    async def embed(self, text: str) -> list[float]:
        data = await self._request(
            "embeddings",
            {"model": settings.AI_EMBEDDING_MODEL, "input": text},
        )
        embedding = data["data"][0]["embedding"]
        if not isinstance(embedding, list) or not all(isinstance(value, (int, float)) for value in embedding):
            raise RuntimeError("AI provider returned an invalid embedding")
        return [float(value) for value in embedding]


def deterministic_embedding(text: str, dimensions: int = 32) -> list[float]:
    """Create a stable lightweight embedding for fallback search and tests."""
    vector = [0.0] * dimensions
    for token in text.lower().split():
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        vector[int.from_bytes(digest[:4], "big") % dimensions] += 1.0
    magnitude = sum(value * value for value in vector) ** 0.5
    return [value / magnitude for value in vector] if magnitude else vector


def get_llm_provider() -> LLMProvider:
    """Construct the configured provider without exposing credentials to callers."""
    if settings.AI_PROVIDER.lower() == "openai":
        return OpenAIProvider()
    return FakeProvider()
