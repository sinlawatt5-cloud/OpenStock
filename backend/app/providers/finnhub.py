"""Finnhub free-tier provider (quotes, market/company news, profiles)."""

from __future__ import annotations

import asyncio
import collections
import logging
import time
from datetime import date, datetime, timedelta, timezone
from typing import Any

import httpx

from ..config import get_settings
from . import ProviderError

logger = logging.getLogger("openstock.finnhub")
BASE = "https://finnhub.io/api/v1"

_calls: collections.deque[float] = collections.deque()
_gate = asyncio.Lock()
_PER_MINUTE = 50


async def _throttle() -> None:
    async with _gate:
        now = time.monotonic()
        while _calls and now - _calls[0] > 60:
            _calls.popleft()
        if len(_calls) >= _PER_MINUTE:
            wait = 60 - (now - _calls[0]) + 0.05
            logger.info("finnhub throttle: waiting %.1fs", wait)
            await asyncio.sleep(max(wait, 0))
            now = time.monotonic()
            while _calls and now - _calls[0] > 60:
                _calls.popleft()
        _calls.append(time.monotonic())


def configured() -> bool:
    return bool(get_settings().finnhub_api_key)


async def _get(path: str, params: dict[str, Any]) -> Any:
    settings = get_settings()
    if not settings.finnhub_api_key:
        raise ProviderError("finnhub key missing")
    await _throttle()
    try:
        async with httpx.AsyncClient(timeout=settings.openstock_http_timeout) as client:
            response = await client.get(
                f"{BASE}{path}",
                params=params,
                headers={"X-Finnhub-Token": settings.finnhub_api_key},
            )
    except httpx.HTTPError as exc:
        raise ProviderError(f"finnhub transport error: {exc}") from exc
    if response.status_code == 429:
        raise ProviderError("finnhub rate limited")
    if response.status_code >= 400:
        raise ProviderError(f"finnhub {response.status_code}")
    try:
        return response.json()
    except ValueError as exc:
        raise ProviderError("finnhub invalid json") from exc


async def quote(symbol: str) -> dict[str, Any]:
    data = await _get("/quote", {"symbol": symbol})
    price = data.get("c")
    if not price:
        raise ProviderError("finnhub quote empty")
    return {
        "symbol": symbol,
        "price": float(price),
        "change": float(data.get("d") or 0),
        "changePct": float(data.get("dp") or 0),
        "prevClose": float(data.get("pc") or price),
        "high": data.get("h"),
        "low": data.get("l"),
        "open": data.get("o"),
        "asOf": datetime.fromtimestamp(
            data.get("t") or time.time(), timezone.utc
        ).isoformat(timespec="seconds"),
        "provider": "finnhub",
    }


def _normalize_news(item: dict[str, Any]) -> dict[str, Any] | None:
    title = item.get("headline")
    if not title:
        return None
    published = item.get("datetime")
    published_at = (
        datetime.fromtimestamp(published, timezone.utc).isoformat(timespec="seconds")
        if isinstance(published, (int, float))
        else None
    )
    related = item.get("related") or ""
    tickers = [t.strip() for t in related.split(",") if t.strip()]
    return {
        "title": title,
        "url": item.get("url"),
        "source": item.get("source") or "Finnhub",
        "publishedAt": published_at,
        "summary": item.get("summary"),
        "tickers": tickers,
        "image": item.get("image"),
    }


async def market_news(limit: int = 30) -> list[dict[str, Any]]:
    data = await _get("/news", {"category": "general"})
    items = [n for n in (_normalize_news(i) for i in data or []) if n]
    items.sort(key=lambda n: n.get("publishedAt") or "", reverse=True)
    return items[:limit]


async def company_news(symbol: str, days: int = 7, limit: int = 8) -> list[dict[str, Any]]:
    today = date.today()
    params = {
        "symbol": symbol,
        "from": (today - timedelta(days=days)).isoformat(),
        "to": today.isoformat(),
    }
    data = await _get("/company-news", params)
    items = [n for n in (_normalize_news(i) for i in data or []) if n]
    for item in items:
        item["tickers"] = item["tickers"] or [symbol]
    items.sort(key=lambda n: n.get("publishedAt") or "", reverse=True)
    return items[:limit]


async def profile(symbol: str) -> dict[str, Any]:
    data = await _get("/stock/profile2", {"symbol": symbol})
    if not data or not data.get("name"):
        raise ProviderError("finnhub profile empty")
    cap = data.get("marketCapitalization")
    return {
        "symbol": data.get("ticker", symbol),
        "name": data.get("name"),
        "logo": data.get("logo"),
        "exchange": data.get("exchange"),
        "industry": data.get("finnhubIndustry"),
        "website": data.get("weburl"),
        "marketCap": float(cap) * 1_000_000 if cap else None,
        "currency": data.get("currency", "USD"),
        "provider": "finnhub",
    }
