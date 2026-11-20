"""JSON REST API fetcher with configurable key mappings."""

from datetime import datetime
from decimal import Decimal
from typing import Any

import httpx

from app.models.opportunity import Source
from app.services.ingestion.base import BaseFetcher, RawOpportunity


def _resolve_json_path(data: Any, path: str) -> Any:
    """Navigate nested dictionary by dot notation (e.g. 'response.data.items')."""
    if not path:
        return data
    current = data
    for part in path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current


class JSONApiFetcher(BaseFetcher):
    """Fetches opportunities from arbitrary JSON REST API endpoints."""

    async def fetch(self, source: Source) -> list[RawOpportunity]:
        config = source.config or {}
        items_path = config.get("items_path", "")
        mapping = config.get("field_mapping", {})

        title_key = mapping.get("title", "title")
        org_key = mapping.get("organization", "organization")
        desc_key = mapping.get("description", "description")
        url_key = mapping.get("url", "url")
        country_key = mapping.get("country", "country")
        fields_key = mapping.get("fields", "fields")
        deadline_key = mapping.get("deadline", "deadline")
        stipend_min_key = mapping.get("stipend_min", "stipend_min")
        stipend_currency_key = mapping.get("stipend_currency", "currency")

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            headers = {"User-Agent": "OpportunityAbroad-Bot/1.0 (+https://opportunityabroad.org)"}
            headers.update(config.get("headers", {}))

            params = config.get("query_params", {})
            response = await client.get(source.url, headers=headers, params=params)
            if response.status_code >= 400:
                raise RuntimeError(f"HTTP fetch error {response.status_code}")
            json_data = response.json()

        raw_list = _resolve_json_path(json_data, items_path) if items_path else json_data
        if not isinstance(raw_list, list):
            if isinstance(raw_list, dict):
                raw_list = [raw_list]
            else:
                return []

        items: list[RawOpportunity] = []
        default_org = config.get("default_organization", source.name)

        for obj in raw_list:
            if not isinstance(obj, dict):
                items.append(
                    RawOpportunity(
                        title="",
                        organization=default_org,
                        description="",
                        source_url="",
                        raw_data={"invalid_item": obj},
                    )
                )
                continue

            title = str(obj.get(title_key, "")).strip()
            url = str(obj.get(url_key, "")).strip()

            description = str(obj.get(desc_key, ""))
            org = str(obj.get(org_key, default_org)).strip() or default_org
            country = obj.get(country_key)

            # Fields / disciplines
            fields_val = obj.get(fields_key, [])
            if isinstance(fields_val, str):
                fields_val = [f.strip() for f in fields_val.split(",") if f.strip()]
            elif not isinstance(fields_val, list):
                fields_val = []

            # Deadline parsing
            deadline_dt = None
            raw_deadline = obj.get(deadline_key)
            if raw_deadline:
                try:
                    deadline_dt = datetime.fromisoformat(str(raw_deadline))
                except Exception:
                    pass

            # Stipend
            stipend_min = None
            if obj.get(stipend_min_key) is not None:
                try:
                    stipend_min = Decimal(str(obj[stipend_min_key]))
                except Exception:
                    pass

            items.append(
                RawOpportunity(
                    title=title,
                    organization=org,
                    description=description,
                    source_url=url,
                    canonical_url=url,
                    country=str(country) if country else None,
                    fields=fields_val,
                    stipend_amount_min=stipend_min,
                    stipend_currency=str(obj.get(stipend_currency_key)) if obj.get(stipend_currency_key) else None,
                    deadline=deadline_dt,
                    raw_data=obj,
                )
            )

        return items
