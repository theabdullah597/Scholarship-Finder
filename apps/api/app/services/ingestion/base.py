"""Base abstractions and data contracts for opportunity ingestion."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.models.opportunity import Source


@dataclass
class RawOpportunity:
    """Standardized intermediate representation of scraped/fetched opportunity data."""

    title: str
    organization: str
    description: str
    source_url: str
    canonical_url: str | None = None
    country: str | None = None
    fields: list[str] = field(default_factory=list)
    kind: str | None = None
    funding_type: str | None = None
    stipend_amount_min: Decimal | None = None
    stipend_amount_max: Decimal | None = None
    stipend_currency: str | None = None
    deadline: datetime | None = None
    tags: list[str] = field(default_factory=list)
    raw_data: dict[str, Any] = field(default_factory=dict)


class BaseFetcher(ABC):
    """Abstract base class for all source fetchers (RSS, JSON API, HTML)."""

    @abstractmethod
    async def fetch(self, source: Source) -> list[RawOpportunity]:
        """Fetch raw opportunity items from the designated source."""
        pass

