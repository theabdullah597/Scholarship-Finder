"""RSS and Atom feed fetcher."""

from datetime import UTC, datetime
from time import mktime
from typing import Any

import feedparser
import httpx

from app.models.opportunity import Source
from app.services.ingestion.base import BaseFetcher, RawOpportunity


class RSSFetcher(BaseFetcher):
    """Fetches opportunities from RSS 2.0 and Atom feeds."""

    async def fetch(self, source: Source) -> list[RawOpportunity]:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            headers = {"User-Agent": "OpportunityAbroad-Bot/1.0 (+https://opportunityabroad.org)"}
            custom_headers = source.config.get("headers", {})
            headers.update(custom_headers)

            response = await client.get(source.url, headers=headers)
            if response.status_code >= 400:
                raise RuntimeError(f"HTTP fetch error {response.status_code}")
            content = response.text

        # feedparser can parse strings directly
        feed: Any = feedparser.parse(content)
        items: list[RawOpportunity] = []

        default_org = source.config.get("default_organization", source.name)
        default_country = source.config.get("default_country", None)

        for entry in feed.entries:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            if not title or not link:
                continue

            # Summary / Description
            description = entry.get("summary", "") or entry.get("description", "")
            if hasattr(entry, "content") and entry.content:
                description = entry.content[0].value

            # Deadline or published date
            deadline_dt = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                deadline_dt = datetime.fromtimestamp(mktime(entry.published_parsed), tz=UTC)

            # Category / Tags / Fields
            tags = []
            if hasattr(entry, "tags"):
                tags = [t.term for t in entry.tags if hasattr(t, "term") and t.term]

            items.append(
                RawOpportunity(
                    title=title,
                    organization=default_org,
                    description=description,
                    source_url=link,
                    canonical_url=link,
                    country=default_country,
                    fields=tags[:3] if tags else [],
                    tags=tags,
                    deadline=deadline_dt,
                    raw_data=dict(entry),
                )
            )

        return items
