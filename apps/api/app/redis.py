from redis.asyncio import Redis, from_url

from app.config import settings

redis_client: Redis | None = None


async def get_redis_client() -> Redis:
    global redis_client
    if redis_client is None:
        redis_client = from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return redis_client


async def close_redis() -> None:
    global redis_client
    if redis_client is not None:
        await redis_client.close()
        redis_client = None
