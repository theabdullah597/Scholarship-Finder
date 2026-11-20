"""Small Redis-backed fixed-window rate limiter for authentication endpoints."""

import logging

from redis.exceptions import RedisError

from app.redis import get_redis_client

logger = logging.getLogger("opportunityabroad.rate_limit")


async def allow_request(key: str, limit: int, window_seconds: int) -> tuple[bool, int]:
    """Return whether a request is allowed and the approximate remaining quota."""
    try:
        redis = await get_redis_client()
        count = int(await redis.incr(key))
        if count == 1:
            await redis.expire(key, window_seconds)
        return count <= limit, max(0, limit - count)
    except (RedisError, OSError, TimeoutError) as exc:
        logger.warning("Rate limiter unavailable; allowing request: %s", type(exc).__name__)
        return True, limit
