import asyncio

import pytest

from app.cache import TTLCache


@pytest.mark.asyncio
async def test_fresh_hit_does_not_reload(db):
    cache = TTLCache(db)
    calls = {"n": 0}

    async def loader():
        calls["n"] += 1
        return {"value": calls["n"]}

    value, meta = await cache.get_or_load("k", 60, loader)
    assert value == {"value": 1}
    assert meta.stale is False

    value2, meta2 = await cache.get_or_load("k", 60, loader)
    assert value2 == {"value": 1}
    assert calls["n"] == 1
    assert meta2.stale is False


@pytest.mark.asyncio
async def test_expired_entry_returns_stale_and_refreshes(db):
    cache = TTLCache(db)
    db.cache_set("k", {"value": "old"}, 0)
    await asyncio.sleep(0.02)
    calls = {"n": 0}

    async def loader():
        calls["n"] += 1
        return {"value": "new"}

    value, meta = await cache.get_or_load("k", 0.001, loader)
    assert value == {"value": "old"}
    assert meta.stale is True

    await asyncio.sleep(0.1)
    assert calls["n"] == 1
    assert cache.peek("k") == {"value": "new"}


@pytest.mark.asyncio
async def test_failure_serves_stale_cache(db):
    cache = TTLCache(db)
    db.cache_set("k", {"value": "last-good"}, 0)
    await asyncio.sleep(0.02)

    async def boom():
        raise RuntimeError("upstream down")

    value, meta = await cache.get_or_load("k", 0.001, boom)
    assert value == {"value": "last-good"}
    assert meta.stale is True
    await asyncio.sleep(0.05)


@pytest.mark.asyncio
async def test_single_flight_loader(db):
    cache = TTLCache(db)
    calls = {"n": 0}

    async def loader():
        calls["n"] += 1
        await asyncio.sleep(0.05)
        return {"value": calls["n"]}

    results = await asyncio.gather(
        cache.get_or_load("same", 60, loader),
        cache.get_or_load("same", 60, loader),
    )
    assert calls["n"] == 1
    assert results[0][0] == {"value": 1}
    assert results[1][0] == {"value": 1}
