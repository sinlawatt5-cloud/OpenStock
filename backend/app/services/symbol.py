"""Per-symbol data: quote, profile, history, levels, peers."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from ..cache import CacheMeta, get_cache
from ..data.universe import BENCHMARK
from ..db import get_db
from ..providers import ProviderError, alphavantage, finnhub, yahoo
from .common import with_meta
from .levels import compute_levels

logger = logging.getLogger("openstock.symbol")

RANGES: dict[str, tuple[str, str]] = {
    "1d": ("5d", "5m"),
    "5d": ("5d", "30m"),
    "1mo": ("1mo", "1d"),
    "6mo": ("6mo", "1d"),
    "1y": ("1y", "1d"),
    "5y": ("5y", "1wk"),
}

HISTORY_TTL = 600
QUOTE_TTL = 300
PROFILE_TTL = 24 * 3600


def _normalize(symbol: str) -> str:
    return symbol.strip().upper()


def _last_session(bars: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not bars:
        return bars
    last_day = bars[-1]["dt"][:10]
    return [b for b in bars if b["dt"][:10] == last_day]


async def get_history(symbol: str, range_key: str = "1y") -> dict[str, Any]:
    symbol = _normalize(symbol)
    range_key = range_key if range_key in RANGES else "1y"
    period, interval = RANGES[range_key]
    cache = get_cache()

    async def load() -> dict[str, Any]:
        try:
            data = await yahoo.history([symbol], period=period, interval=interval)
            bars = data.get(symbol) or next(iter(data.values()), [])
            provider = "yfinance"
        except ProviderError:
            bars = await alphavantage.daily(symbol)
            provider = "alphavantage"
        if range_key == "1d":
            bars = _last_session(bars)
        return {"bars": bars, "provider": provider}

    payload, meta = await cache.get_or_load(
        f"symbol:history:{symbol}:{range_key}", HISTORY_TTL, load
    )
    bars = payload["bars"]
    record = get_db().get_symbol(symbol) or {}
    return with_meta(
        {
            "symbol": symbol,
            "name": record.get("name"),
            "nameTh": record.get("name_th"),
            "range": range_key,
            "interval": interval,
            "bars": bars,
            "last": bars[-1] if bars else None,
        },
        meta,
        payload.get("provider", "yfinance"),
    )


async def get_quote(symbol: str) -> dict[str, Any]:
    symbol = _normalize(symbol)
    cache = get_cache()

    async def load() -> dict[str, Any]:
        try:
            data = await yahoo.history([symbol], period="1mo", interval="1d")
            bars = data.get(symbol) or next(iter(data.values()), [])
            if len(bars) < 2:
                raise ProviderError("not enough bars")
            last, prev = bars[-1], bars[-2]
            return {
                "price": round(last["c"], 2),
                "change": round(last["c"] - prev["c"], 2),
                "changePct": round((last["c"] / prev["c"] - 1) * 100, 2),
                "volume": last.get("v"),
                "prevClose": round(prev["c"], 2),
                "provider": "yfinance",
            }
        except ProviderError:
            pass
        try:
            q = await finnhub.quote(symbol)
            return {
                "price": round(q["price"], 2),
                "change": round(q["change"], 2),
                "changePct": round(q["changePct"], 2),
                "volume": None,
                "prevClose": round(q["prevClose"], 2),
                "provider": "finnhub",
            }
        except ProviderError:
            q = await alphavantage.quote(symbol)
            return {
                "price": round(q["price"], 2),
                "change": round(q["change"], 2),
                "changePct": round(q["changePct"], 2),
                "volume": q.get("volume"),
                "prevClose": round(q["prevClose"], 2),
                "provider": "alphavantage",
            }

    payload, meta = await cache.get_or_load(
        f"symbol:quote:{symbol}", QUOTE_TTL, load
    )
    record = get_db().get_symbol(symbol)
    return with_meta(
        {
            "symbol": symbol,
            **payload,
            "name": (record or {}).get("name"),
            "nameTh": (record or {}).get("name_th"),
            "sector": (record or {}).get("sector"),
            "industry": (record or {}).get("industry"),
        },
        meta,
        payload.get("provider", "yfinance"),
    )


async def get_profile(symbol: str) -> dict[str, Any]:
    symbol = _normalize(symbol)
    cache = get_cache()
    record = get_db().get_symbol(symbol) or {}

    async def load() -> dict[str, Any]:
        yahoo_data: dict[str, Any] | None = None
        try:
            yahoo_data = await yahoo.profile(symbol)
            if yahoo_data.get("summary") and yahoo_data.get("marketCap"):
                return {**yahoo_data, "provider": "yfinance"}
        except ProviderError:
            pass
        try:
            fh = await finnhub.profile(symbol)
            merged = {**fh, **(yahoo_data or {})}
            # keep the richer fields from each provider
            merged["marketCap"] = (yahoo_data or {}).get("marketCap") or fh.get("marketCap")
            merged["logo"] = (yahoo_data or {}).get("logo") or fh.get("logo")
            merged["summary"] = (yahoo_data or {}).get("summary")
            merged["provider"] = "yfinance+finnhub" if yahoo_data else "finnhub"
            return merged
        except ProviderError:
            if yahoo_data:
                return {**yahoo_data, "provider": "yfinance"}
            return {
                "symbol": symbol,
                "name": record.get("name", symbol),
                "logo": None,
                "exchange": record.get("exchange"),
                "industry": record.get("industry"),
                "website": None,
                "marketCap": None,
                "currency": "USD",
                "provider": "local",
            }

    payload, meta = await cache.get_or_load(
        f"symbol:profile:v2:{symbol}", PROFILE_TTL, load
    )
    merged = {
        **payload,
        "nameTh": record.get("name_th"),
        "sector": payload.get("sector") or record.get("sector"),
        "industry": payload.get("industry") or record.get("industry"),
    }
    return with_meta(merged, meta, payload.get("provider", "local"))


async def get_levels(symbol: str, range_key: str = "1y", method: str = "structure") -> dict[str, Any]:
    history = await get_history(symbol, range_key)
    method = method if method in {"structure", "pivot"} else "structure"
    result = compute_levels(history["bars"], method=method)
    return {
        **result,
        "symbol": _normalize(symbol),
        "range": history["range"],
        "stale": history["stale"],
        "asOf": history["asOf"],
        "ageSeconds": history["ageSeconds"],
        "provider": history["provider"],
    }


async def get_symbol_page(symbol: str) -> dict[str, Any]:
    symbol = _normalize(symbol)
    quote, profile = await asyncio.gather(
        get_quote(symbol), get_profile(symbol), return_exceptions=True
    )
    if isinstance(quote, Exception):
        raise quote
    if isinstance(profile, Exception):
        profile = {"symbol": symbol, "name": symbol}
    sector = profile.get("sector") or quote.get("sector") or ""
    peers = get_db().peers(sector, symbol) if sector else []
    return {
        "symbol": symbol,
        "quote": quote,
        "profile": profile,
        "peers": [
            {
                "symbol": p["symbol"],
                "name": p["name"],
                "nameTh": p["name_th"],
                "sector": p["sector"],
            }
            for p in peers
        ],
        "benchmark": BENCHMARK,
    }


def _cache_meta_now() -> CacheMeta:
    from datetime import datetime, timezone

    return CacheMeta(False, datetime.now(timezone.utc).isoformat(timespec="seconds"), 0)
