from datetime import datetime
from typing import Any

from app.core.config import get_settings

_settings = get_settings()

_redis = None
try:
    from redis.asyncio import Redis
    _redis = Redis.from_url(_settings.redis_url, encoding="utf-8", decode_responses=True)
except Exception:
    _redis = None

# In-memory fallback so SQLite-only runs work without Redis.
_mem_refresh: dict[str, str] = {}
_mem_location: dict[str, dict[str, Any]] = {}


async def _redis_ok() -> bool:
    if _redis is None:
        return False
    try:
        await _redis.ping()
        return True
    except Exception:
        return False


async def store_refresh_token(user_id: int, token: str, ttl_seconds: int) -> None:
    key = f"driver:{user_id}:refresh"
    if await _redis_ok():
        await _redis.set(key, token, ex=ttl_seconds)
    else:
        _mem_refresh[key] = token


async def get_refresh_token(user_id: int) -> str | None:
    key = f"driver:{user_id}:refresh"
    if await _redis_ok():
        return await _redis.get(key)
    return _mem_refresh.get(key)


async def store_driver_location(user_id: int, latitude: float, longitude: float) -> None:
    key = f"driver:{user_id}:location"
    payload: dict[str, Any] = {
        "lat": latitude,
        "lng": longitude,
        "updated_at": datetime.utcnow().isoformat()
    }
    if await _redis_ok():
        await _redis.hset(key, mapping=payload)
        await _redis.expire(key, 900)
    else:
        _mem_location[key] = payload


async def get_driver_location(user_id: int) -> dict[str, Any] | None:
    key = f"driver:{user_id}:location"
    if await _redis_ok():
        result = await _redis.hgetall(key)
        return result or None
    return _mem_location.get(key) or None


# Backwards-compat: `from app.services.cache import redis` still works;
# it is None when Redis is unreachable (in-memory fallback active).
redis = _redis
