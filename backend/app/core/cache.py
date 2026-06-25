"""
GER2 CMMS — Redis Cache Layer
Provides get/set helpers with JSON serialisation and TTL.
"""
import json
from typing import Any, Optional

import redis.asyncio as aioredis

from app.core.config import settings

_redis_pool: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
        )
    return _redis_pool


async def cache_get(key: str) -> Optional[Any]:
    r = await get_redis()
    raw = await r.get(key)
    return json.loads(raw) if raw is not None else None


async def cache_set(key: str, value: Any, ttl: int = settings.CACHE_TTL_DEFAULT) -> None:
    r = await get_redis()
    await r.setex(key, ttl, json.dumps(value, default=str))


async def cache_delete(key: str) -> None:
    r = await get_redis()
    await r.delete(key)


async def cache_invalidate_pattern(pattern: str) -> int:
    r = await get_redis()
    keys = await r.keys(pattern)
    if keys:
        return await r.delete(*keys)
    return 0
