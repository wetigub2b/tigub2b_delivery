from datetime import datetime
from typing import Any

from redis.asyncio import Redis

from app.core.config import get_settings

_settings = get_settings()

redis = Redis.from_url(_settings.redis_url, encoding="utf-8", decode_responses=True)


async def store_refresh_token(user_id: int, token: str, ttl_seconds: int) -> None:
    key = f"driver:{user_id}:refresh"
    await redis.set(key, token, ex=ttl_seconds)


async def get_refresh_token(user_id: int) -> str | None:
    key = f"driver:{user_id}:refresh"
    return await redis.get(key)


async def store_driver_location(user_id: int, latitude: float, longitude: float) -> None:
    key = f"driver:{user_id}:location"
    payload: dict[str, Any] = {
        "lat": latitude,
        "lng": longitude,
        "updated_at": datetime.utcnow().isoformat()
    }
    await redis.hset(key, mapping=payload)
    await redis.expire(key, 900)


async def get_driver_location(user_id: int) -> dict[str, Any] | None:
    key = f"driver:{user_id}:location"
    result = await redis.hgetall(key)
    return result or None
