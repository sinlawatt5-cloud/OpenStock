"""Stale-while-revalidate cache on top of SQLite with single-flight refresh."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

from .db import Database, get_db

logger = logging.getLogger("openstock.cache")


@dataclass
class CacheMeta:
    stale: bool
    as_of: str
    age_seconds: int

    def as_dict(self) -> dict[str, Any]:
        return {"stale": self.stale, "asOf": self.as_of, "ageSeconds": self.age_seconds}


def _iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).isoformat(timespec="seconds")


class TTLCache:
    def __init__(self, db: Database | None = None) -> None:
        self.db = db or get_db()
        self._locks: dict[str, asyncio.Lock] = {}
        self._inflight: set[str] = set()
        self._tasks: set[asyncio.Task] = set()

    def _lock(self, key: str) -> asyncio.Lock:
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        return self._locks[key]

    async def get_or_load(
        self,
        key: str,
        ttl: float,
        loader: Callable[[], Awaitable[Any]],
        *,
        force: bool = False,
    ) -> tuple[Any, CacheMeta]:
        entry = self.db.cache_get(key)
        now = time.time()

        if entry and not force and now - entry.stored_at < ttl:
            return entry.value, CacheMeta(False, _iso(entry.stored_at), int(now - entry.stored_at))

        if entry and not force:
            self._spawn_refresh(key, ttl, loader)
            return entry.value, CacheMeta(True, _iso(entry.stored_at), int(now - entry.stored_at))

        async with self._lock(key):
            entry = self.db.cache_get(key)
            if entry and not force and time.time() - entry.stored_at < ttl:
                return entry.value, CacheMeta(
                    False, _iso(entry.stored_at), int(time.time() - entry.stored_at)
                )
            try:
                value = await loader()
            except Exception:
                if entry:
                    logger.warning("refresh failed for %s, serving stale cache", key)
                    self._spawn_refresh(key, ttl, loader)
                    return entry.value, CacheMeta(
                        True, _iso(entry.stored_at), int(time.time() - entry.stored_at)
                    )
                raise
            self.db.cache_set(key, value, ttl)
            return value, CacheMeta(False, _iso(time.time()), 0)

    def _spawn_refresh(
        self,
        key: str,
        ttl: float,
        loader: Callable[[], Awaitable[Any]],
    ) -> None:
        if key in self._inflight:
            return
        self._inflight.add(key)

        async def run() -> None:
            try:
                value = await loader()
                self.db.cache_set(key, value, ttl)
            except Exception as exc:  # keep stale data, log only
                logger.warning("background refresh failed for %s: %s", key, exc)
            finally:
                self._inflight.discard(key)

        try:
            task = asyncio.create_task(run())
        except RuntimeError:
            self._inflight.discard(key)
            return
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    def prefetch(self, key: str, ttl: float, loader: Callable[[], Awaitable[Any]]) -> None:
        """Warm a key in the background without blocking the caller."""
        entry = self.db.cache_get(key)
        if entry and time.time() - entry.stored_at < ttl:
            return
        self._spawn_refresh(key, ttl, loader)

    def peek(self, key: str) -> Any | None:
        entry = self.db.cache_get(key)
        return entry.value if entry else None


_cache: TTLCache | None = None


def get_cache() -> TTLCache:
    global _cache
    if _cache is None:
        _cache = TTLCache()
    return _cache
