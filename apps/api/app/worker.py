"""Background worker daemon and scheduler for scheduled source ingestion."""

import asyncio
import logging
import signal
import sys
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import AsyncSessionLocal
from app.models.opportunity import Source
from app.services.ingestion.engine import IngestionEngine

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] [worker] %(message)s",
)
logger = logging.getLogger("opportunityabroad.worker")


async def run_due_sources(db: AsyncSession) -> int:
    """Find and execute ingestion for all active sources that are due based on fetch_interval_minutes.

    Returns the count of sources ingested.
    """
    now = datetime.now(UTC)

    # Find active sources
    stmt = select(Source).where(Source.is_active.is_(True))
    sources = list((await db.execute(stmt)).scalars().all())

    due_sources = []
    for s in sources:
        if s.last_run_at is None:
            due_sources.append(s)
        else:
            elapsed = now - s.last_run_at
            if elapsed >= timedelta(minutes=s.fetch_interval_minutes):
                due_sources.append(s)

    logger.info("Scheduler checked sources: %d active, %d due for ingestion", len(sources), len(due_sources))

    for source in due_sources:
        try:
            await IngestionEngine.run_ingestion_for_source(db, source)
        except Exception as exc:
            logger.error("Failed executing scheduled run for source '%s': %s", source.name, exc)

    return len(due_sources)


class WorkerDaemon:
    """Continuous background scheduler daemon."""

    def __init__(self, check_interval_seconds: int = 60) -> None:
        self.running = True
        self.check_interval_seconds = check_interval_seconds

    def stop(self) -> None:
        logger.info("Stopping OpportunityAbroad worker daemon...")
        self.running = False

    async def run(self) -> None:
        logger.info("Starting OpportunityAbroad background worker daemon...")
        logger.info("Worker scheduler active (polling interval: %d seconds)", self.check_interval_seconds)

        while self.running:
            try:
                async with AsyncSessionLocal() as session:
                    await run_due_sources(session)
            except Exception as exc:
                logger.error("Error during scheduled source check: %s", exc)

            # Sleep in small increments to allow rapid shutdown
            for _ in range(self.check_interval_seconds):
                if not self.running:
                    break
                await asyncio.sleep(1)

        logger.info("OpportunityAbroad worker terminated cleanly.")


def main() -> None:
    worker = WorkerDaemon()

    def signal_handler(signum: int, frame: object) -> None:
        logger.info("Received termination signal %s", signum)
        worker.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        asyncio.run(worker.run())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Worker stopped by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()
