import asyncio
import logging
import signal
import sys

from app.config import settings

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] [worker] %(message)s",
)
logger = logging.getLogger("opportunityabroad.worker")


class WorkerDaemon:
    def __init__(self) -> None:
        self.running = True

    def stop(self) -> None:
        logger.info("Stopping OpportunityAbroad worker daemon...")
        self.running = False

    async def run(self) -> None:
        logger.info("Starting OpportunityAbroad background worker daemon...")
        logger.info("Worker placeholder ready: waiting for scheduled ingestion and reminder jobs.")

        while self.running:
            try:
                # Placeholder heartbeat every 30 seconds
                await asyncio.sleep(30)
                if self.running:
                    logger.debug("Worker daemon heartbeat tick.")
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("Unexpected worker error: %s", exc)

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
