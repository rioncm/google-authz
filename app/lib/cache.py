import asyncio
import json
import time
from dataclasses import dataclass
from typing import Optional

from redis.asyncio import Redis

from app.lib.config import Settings
from app.lib.models import EffectiveAuth


@dataclass
class CacheRecord:
    """EffectiveAuth cached entry with expiry tracking."""

    effective_auth: EffectiveAuth
    expires_at: float

    @property
    def ttl_remaining(self) -> float:
        return max(0.0, self.expires_at - time.time())


class EffectiveAuthCache:
    """Abstract cache interface."""

    async def get(self, key: str) -> Optional[CacheRecord]:  # pragma: no cover - interface
        raise NotImplementedError

    async def set(self, key: str, effective_auth: EffectiveAuth, ttl_seconds: int) -> None:  # pragma: no cover
        raise NotImplementedError

    async def delete(self, key: str) -> None:  # pragma: no cover
        raise NotImplementedError

    async def close(self) -> None:  # pragma: no cover
        raise NotImplementedError


class InMemoryCache(EffectiveAuthCache):
    """Simple in-memory cache for development/test usage."""

    def __init__(self) -> None:
        self._store: dict[str, CacheRecord] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[CacheRecord]:
        async with self._lock:
            record = self._store.get(key)
            if not record:
                return None
            if record.expires_at <= time.time():
                self._store.pop(key, None)
                return None
            return record

    async def set(self, key: str, effective_auth: EffectiveAuth, ttl_seconds: int) -> None:
        expires_at = time.time() + ttl_seconds
        async with self._lock:
            self._store[key] = CacheRecord(effective_auth=effective_auth, expires_at=expires_at)

    async def delete(self, key: str) -> None:
        async with self._lock:
            self._store.pop(key, None)

    async def close(self) -> None:
        async with self._lock:
            self._store.clear()


class RedisCache(EffectiveAuthCache):
    """Redis-based cache implementation."""

    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def get(self, key: str) -> Optional[CacheRecord]:
        payload = await self._redis.get(key)
        if not payload:
            return None
        data = json.loads(payload)
        expires_at = float(data.get("expires_at", 0))
        effective_auth = EffectiveAuth(**data["effective_auth"])
        if expires_at <= time.time():
            await self._redis.delete(key)
            return None
        return CacheRecord(effective_auth=effective_auth, expires_at=expires_at)

    async def set(self, key: str, effective_auth: EffectiveAuth, ttl_seconds: int) -> None:
        expires_at = time.time() + ttl_seconds
        payload = json.dumps(
            {
                "effective_auth": effective_auth.model_dump(mode="json"),
                "expires_at": expires_at,
            }
        )
        await self._redis.set(key, payload, ex=ttl_seconds)

    async def delete(self, key: str) -> None:
        await self._redis.delete(key)

    async def close(self) -> None:
        await self._redis.aclose()


async def build_cache(settings: Settings) -> EffectiveAuthCache:
    """Create the appropriate cache backend."""
    if settings.redis_url:
        redis = Redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
        return RedisCache(redis)
    return InMemoryCache()
