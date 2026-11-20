"""HTML Web Scraper fetcher using CSS selectors and BeautifulSoup."""

from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.models.opportunity import Source
from app.services.ingestion.base import BaseFetcher, RawOpportunity


class HTMLScraperFetcher(BaseFetcher):
    """Fetches opportunities from HTML listing pages using configurable CSS selectors."""

    async def fetch(self, source: Source) -> list[RawOpportunity]:
        config = source.config or {}
        card_selector = config.get("card_selector", "article, .opportunity-card, .scholarship-item, .listing-card")
        title_selector = config.get("title_selector", "h2, h3, .title, a")
        link_selector = config.get("link_selector", "a")
        desc_selector = config.get("desc_selector", "p, .description, .summary")
        org_selector = config.get("org_selector", ".organization, .institution, .provider")

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            headers = {"User-Agent": "OpportunityAbroad-Bot/1.0 (+https://opportunityabroad.org)"}
            headers.update(config.get("headers", {}))

            response = await client.get(source.url, headers=headers)
            if response.status_code >= 400:
                raise RuntimeError(f"HTTP fetch error {response.status_code}")
            html_text = response.text

        soup = BeautifulSoup(html_text, "html.parser")
        cards = soup.select(card_selector)
        if not cards:
            # Fallback: if card selector not found, search all anchor tags with meaningful text
            cards = soup.find_all("article") or soup.find_all("div", class_=lambda c: c and "item" in c)

        items: list[RawOpportunity] = []
        default_org = config.get("default_organization", source.name)
        default_country = config.get("default_country", None)

        for card in cards:
            # Extract title
            title_tag = card.select_one(title_selector)
            title = title_tag.get_text(strip=True) if title_tag else ""
            if not title:
                continue

            # Extract link
            link_tag = card.select_one(link_selector)
            href_value = link_tag.get("href", "") if link_tag else ""
            href = href_value if isinstance(href_value, str) else ""
            if not href and title_tag and title_tag.name == "a":
                title_href = title_tag.get("href", "")
                href = title_href if isinstance(title_href, str) else ""

            if not href:
                continue

            # Resolve relative link to absolute URL
            full_url = urljoin(source.url, href)

            # Extract description
            desc_tag = card.select_one(desc_selector)
            description = desc_tag.get_text(separator=" ", strip=True) if desc_tag else title

            # Extract organization
            org_tag = card.select_one(org_selector) if org_selector else None
            org = org_tag.get_text(strip=True) if org_tag else default_org

            items.append(
                RawOpportunity(
                    title=title,
                    organization=org or default_org,
                    description=description,
                    source_url=full_url,
                    canonical_url=full_url,
                    country=default_country,
                    raw_data={"html_snippet": str(card)[:500]},
                )
            )

        return items
