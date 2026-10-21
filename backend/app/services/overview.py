"""Dashboard overview: index cards, SPY vs 200DMA, market breadth."""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone
from statistics import fmean
from typing import Any

from ..cache import get_cache
from ..data.universe import BREADTH_UNIVERSE, INDICES
from ..providers import ProviderError, finnhub, yahoo
from .common import with_meta

logger = logging.getLogger("openstock.overview")

OVERVIEW_TTL = 300
BREADTH_TTL = 6 * 3600
BREADTH_KEY = "market:breadth"
OVERVIEW_KEY = "market:overview"

_PROXY = {
    "^GSPC": "SPY",
    "^IXIC": "QQQ",
    "^DJI": "DIA",
    "BTC-USD": "BINANCE:BTCUSDT",
    "GC=F": "OANDA:XAU_USD",
}

_breadth_task: asyncio.Task | None = None


async def _load_overview() -> dict[str, Any]:
    symbols = [item["symbol"] for item in INDICES] + ["SPY"]
    provider = "yfinance"
    try:
        bars_by_symbol = await yahoo.history(symbols, period="1y", interval="1d")
    except ProviderError as exc:
        logger.warning("index history failed (%s), trying finnhub quotes", exc)
        bars_by_symbol = {}
        provider = "finnhub"

    indices: list[dict[str, Any]] = []
    for item in INDICES:
        bars = bars_by_symbol.get(item["symbol"], [])
        price = change = change_pct = None
        sparkline: list[float] = []
        if len(bars) >= 2:
            price = round(bars[-1]["c"], 2)
            prev = bars[-2]["c"]
            change = round(price - prev, 2)
            change_pct = round((price / prev - 1) * 100, 2) if prev else None
            sparkline = [round(b["c"], 2) for b in bars[-30:]]
        if price is None and provider == "finnhub":
            try:
                q = await finnhub.quote(_PROXY.get(item["symbol"], item["symbol"]))
                price = round(q["price"], 2)
                change = round(q["change"], 2)
                change_pct = round(q["changePct"], 2)
            except ProviderError:
                pass
        if price is None:
            continue
        indices.append(
            {
                "symbol": item["symbol"],
                "label": item["label"],
                "short": item["short"],
                "kind": item["kind"],
                "price": price,
                "change": change,
                "changePct": change_pct,
                "sparkline": sparkline,
            }
        )

    spy_bars = bars_by_symbol.get("SPY", [])
    spy: dict[str, Any] | None = None
    if len(spy_bars) >= 200:
        closes = [b["c"] for b in spy_bars]
        ma200 = fmean(closes[-200:])
        last = closes[-1]
        prev = closes[-2]
        spy = {
            "price": round(last, 2),
            "changePct": round((last / prev - 1) * 100, 2) if prev else None,
            "ma200": round(ma200, 2),
            "vsMa200Pct": round((last / ma200 - 1) * 100, 2),
            "aboveMa200": last > ma200,
        }

    return {"indices": indices, "spy": spy, "provider": provider}


async def _load_breadth() -> dict[str, Any]:
    bars_by_symbol = await yahoo.history(BREADTH_UNIVERSE, period="1y", interval="1d")
    above = 0
    counted = 0
    for symbol in BREADTH_UNIVERSE:
        bars = bars_by_symbol.get(symbol, [])
        if len(bars) < 200:
            continue
        closes = [b["c"] for b in bars]
        ma200 = fmean(closes[-200:])
        counted += 1
        if closes[-1] > ma200:
            above += 1
    if not counted:
        raise ProviderError("breadth universe had no history")
    return {
        "pctAboveMa200": round(above / counted * 100, 1),
        "above": above,
        "universeSize": counted,
        "provider": "yfinance",
    }


async def get_breadth(*, blocking: bool = False) -> dict[str, Any] | None:
    global _breadth_task
    cache = get_cache()
    entry = cache.db.cache_get(BREADTH_KEY)
    if entry:
        age = int(time.time() - entry.stored_at)
        return {
            **entry.value,
            "stale": age > BREADTH_TTL,
            "ageSeconds": age,
            "asOf": datetime.fromtimestamp(
                entry.stored_at, timezone.utc
            ).isoformat(timespec="seconds"),
        }

    loop = asyncio.get_running_loop()
    if _breadth_task is None or _breadth_task.done():
        _breadth_task = loop.create_task(_refresh_breadth())
    if blocking:
        try:
            return await asyncio.wait_for(asyncio.shield(_breadth_task), timeout=60)
        except Exception as exc:  # pragma: no cover - upstream dependent
            logger.warning("breadth unavailable: %s", exc)
    return None


async def _refresh_breadth() -> dict[str, Any] | None:
    cache = get_cache()
    try:
        data = await _load_breadth()
        cache.db.cache_set(BREADTH_KEY, data, BREADTH_TTL)
        return data
    except Exception as exc:  # pragma: no cover - upstream dependent
        logger.warning("breadth refresh failed: %s", exc)
        return None


async def get_overview() -> dict[str, Any]:
    cache = get_cache()
    payload, meta = await cache.get_or_load(OVERVIEW_KEY, OVERVIEW_TTL, _load_overview)
    breadth = await get_breadth()
    return with_meta(
        {**payload, "breadth": breadth},
        meta,
        payload.get("provider", "yfinance"),
    )
