"""Ingestion Engine coordinating fetchers, normalization, deduplication, and run logging."""

import logging
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ingestion import IngestionRun, IngestionStatus
from app.models.opportunity import Source
from app.services.ingestion.base import BaseFetcher
from app.services.ingestion.dedup import ingest_or_update_opportunity
from app.services.ingestion.html_scraper import HTMLScraperFetcher
from app.services.ingestion.json_api import JSONApiFetcher
from app.services.ingestion.normalizer import normalize_raw_opportunity
from app.services.ingestion.rss import RSSFetcher

logger = logging.getLogger("opportunityabroad.ingestion")


def get_fetcher_for_source(source_type: str) -> BaseFetcher:
    """Factory to retrieve appropriate fetcher instance based on source type."""
    stype = source_type.lower()
    if stype == "rss":
        return RSSFetcher()
    elif stype == "json_api":
        return JSONApiFetcher()
    elif stype == "html_scraper":
        return HTMLScraperFetcher()
    else:
        raise ValueError(f"Unsupported source type: {source_type}")


class IngestionEngine:
    """Coordinates the ingestion pipeline for a given opportunity source."""

    @staticmethod
    async def run_ingestion_for_source(db: AsyncSession, source: Source) -> IngestionRun:
        """Execute full ingestion lifecycle for a source with error boundary protection."""
        logger.info("Starting ingestion run for source '%s' (type: %s, url: %s)", source.name, source.source_type, source.url)

        # 1. Initialize IngestionRun record
        run = IngestionRun(
            source_id=source.id,
            status=IngestionStatus.RUNNING.value,
            items_found=0,
            items_created=0,
            items_updated=0,
            items_failed=0,
            started_at=datetime.now(UTC),
        )
        db.add(run)
        await db.commit()
        await db.refresh(run)

        error_logs: list[str] = []
        fetcher = get_fetcher_for_source(source.source_type)

        try:
            # 2. Fetch raw items
            raw_items = await fetcher.fetch(source)
            run.items_found = len(raw_items)
            logger.info("Source '%s': %d raw items discovered", source.name, len(raw_items))

            # 3. Process each item inside an individual try-except boundary
            for idx, raw in enumerate(raw_items):
                try:
                    normalized = normalize_raw_opportunity(raw)
                    if not normalized.get("title") or not normalized.get("canonical_url"):
                        run.items_failed += 1
                        error_logs.append(f"Item #{idx}: Missing mandatory title or URL. Raw: {raw.title[:30]}")
                        continue

                    _opp, is_created = await ingest_or_update_opportunity(
                        db,
                        source=source,
                        normalized_data=normalized,
                    )

                    if is_created:
                        run.items_created += 1
                    else:
                        run.items_updated += 1

                except Exception as item_err:
                    run.items_failed += 1
                    err_msg = f"Item #{idx} ({getattr(raw, 'title', 'unknown')[:30]}): {item_err}"
                    logger.warning("Item-level ingestion error: %s", err_msg)
                    error_logs.append(err_msg)

            # Commit updates to database
            source.last_run_at = datetime.now(UTC)
            await db.commit()

        except Exception as fetch_err:
            run.items_failed += 1
            catastrophic_msg = f"Fatal source fetch failure for '{source.name}': {fetch_err}"
            logger.error(catastrophic_msg)
            error_logs.append(catastrophic_msg)

        # 4. Finalize run status
        run.finished_at = datetime.now(UTC)
        if error_logs:
            run.error_log = "\n".join(error_logs[:100])  # Cap at 100 log lines

        if run.items_failed == 0 and (run.items_created > 0 or run.items_updated > 0 or run.items_found == 0):
            run.status = IngestionStatus.SUCCESS.value
        elif (run.items_created > 0 or run.items_updated > 0) and run.items_failed > 0:
            run.status = IngestionStatus.PARTIAL_FAILURE.value
        else:
            run.status = IngestionStatus.FAILED.value

        await db.commit()
        await db.refresh(run)

        logger.info(
            "Completed ingestion for '%s' (status: %s, found: %d, created: %d, updated: %d, failed: %d)",
            source.name,
            run.status,
            run.items_found,
            run.items_created,
            run.items_updated,
            run.items_failed,
        )
        return run

