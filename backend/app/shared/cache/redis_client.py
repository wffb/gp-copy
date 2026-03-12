from __future__ import annotations

import logging
from typing import Annotated, Optional, Dict

from fastapi import Depends, HTTPException, Request, status
from redis.asyncio import Redis

from app.shared.config import settings


class _InMemoryRedis:
    """Minimal async Redis-like store for tests/local when REDIS_URL is not set.

    Implements only methods used by SessionRepository: set/get/delete/aclose.
    TTL handling is best-effort: keys are stored with expiry timestamps and
    evaluated on access; a background janitor is intentionally omitted.
    """

    def __init__(self) -> None:
        self._store: Dict[str, tuple[str, Optional[float]]] = {}

    async def set(self, key: str, value: str, ex: Optional[int] = None) -> None:
        expires_at = None
        if ex is not None:
            expires_at = __import__("time").time() + float(ex)
        self._store[key] = (value, expires_at)

    async def get(self, key: str) -> Optional[str]:
        import time

        item = self._store.get(key)
        if not item:
            return None
        value, expires_at = item
        if expires_at is not None and time.time() >= expires_at:
            # Expired; remove and behave like missing
            self._store.pop(key, None)
            return None
        return value

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def aclose(self) -> None:  # for parity with redis client
        self._store.clear()


async def init_redis(app) -> None:
    app.state.redis = None
    if not settings.redis_url:
        logging.getLogger(__name__).info("REDIS_URL not set; using in-memory store for sessions")
        app.state.redis = _InMemoryRedis()
        return
    client = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        await client.ping()
    except Exception as e:
        logging.getLogger(__name__).error("Redis ping failed: %s; falling back to in-memory store", e)
        app.state.redis = _InMemoryRedis()
        return
    app.state.redis = client


async def close_redis(app) -> None:
    redis: Redis | None = getattr(app.state, "redis", None)
    if redis is not None:
        await redis.aclose()


def get_redis(request: Request) -> Redis:
    redis: Redis | None = getattr(request.app.state, "redis", None)
    if redis is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Redis not configured")
    return redis


RedisDep = Annotated[Redis, Depends(get_redis)]
