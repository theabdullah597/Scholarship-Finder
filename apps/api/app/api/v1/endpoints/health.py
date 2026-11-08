from datetime import datetime, timezone
import logging
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.redis import get_redis_client

logger = logging.getLogger(__name__)

router = APIRouter()


class HealthCheckResponse(BaseModel):
    status: str
    db: str
    redis: str
    version: str
    timestamp: str


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="Service Health Check",
    description="Returns database and redis connectivity status.",
)
async def health_check(
    db: AsyncSession = Depends(get_db),
) -> HealthCheckResponse:
    # Check Database
    db_status = "connected"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        logger.warning("Database health check failed: %s", exc)
        db_status = "disconnected"

    # Check Redis
    redis_status = "connected"
    try:
        redis = await get_redis_client()
        pong = await redis.ping()
        if not pong:
            redis_status = "disconnected"
    except Exception as exc:
        logger.warning("Redis health check failed: %s", exc)
        redis_status = "disconnected"

    overall_status = "ok" if (db_status == "connected" and redis_status == "connected") else "degraded"

    return HealthCheckResponse(
        status=overall_status,
        db=db_status,
        redis=redis_status,
        version="0.1.0",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

