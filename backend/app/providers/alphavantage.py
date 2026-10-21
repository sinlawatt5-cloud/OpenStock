"""Alpha Vantage fallback provider.

Free tier allows ~25 requests/day, so every call goes through a hard daily cap
stored in SQLite. Used only when the primary providers fail.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import httpx

from ..config import get_settings
from ..db import get_db
from . import ProviderError

logger = logging.getLogger("openstock.alphavantage")
BASE = "https://www.alphavantage.co/query"


def configured() -> bool:
    return bool(get_settings().alphavantage_api_key)


async def _get(params: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    if not settings.alphavantage_api_key:
        raise ProviderError("alphavantage key missing")
    if not get_db().try_consume("alphavantage", cap=settings.alphavantage_daily_cap):
        raise ProviderError("alphavantage daily cap reached")
    query = {**params, "apikey": settings.alphavantage_api_key}
    try:
        async with httpx.AsyncClient(timeout=settings.openstock_http_timeout) as client:
            response = await client.get(BASE, params=query)
            response.raise_for_status()
            data = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise ProviderError(f"alphavantage error: {exc}") from exc
    if "Note" in data or "Information" in data or "Error Message" in data:
        raise ProviderError("alphavantage quota or request error")
    return data


async def quote(symbol: str) -> dict[str, Any]:
    data = await _get({"function": "GLOBAL_QUOTE", "symbol": symbol})
    q = data.get("Global Quote") or {}
    price = q.get("05. price")
    if not price:
        raise ProviderError("alphavantage quote empty")
    price_f = float(price)
    prev = float(q.get("08. previous close") or price_f)
    change = float(q.get("09. change") or (price_f - prev))
    pct = float((q.get("10. change percent") or "0").replace("%", ""))
    return {
        "symbol": symbol,
        "price": price_f,
        "change": change,
        "changePct": pct,
        "prevClose": prev,
        "volume": float(q.get("06. volume") or 0),
        "asOf": q.get("07. latest trading day"),
        "provider": "alphavantage",
    }


async def daily(symbol: str, outputsize: str = "compact") -> list[dict[str, Any]]:
    data = await _get(
        {"function": "TIME_SERIES_DAILY", "symbol": symbol, "outputsize": outputsize}
    )
    series = data.get("Time Series (Daily)") or {}
    bars = []
    for day, row in sorted(series.items()):
        bars.append(
            {
                "t": int(datetime.fromisoformat(day).timestamp()),
                "dt": f"{day}T00:00Z",
                "o": float(row["1. open"]),
                "h": float(row["2. high"]),
                "l": float(row["3. low"]),
                "c": float(row["4. close"]),
                "v": float(row["5. volume"]),
            }
        )
    if not bars:
        raise ProviderError("alphavantage daily empty")
    return bars


async def news(limit: int = 30) -> list[dict[str, Any]]:
    data = await _get(
        {"function": "NEWS_SENTIMENT", "topics": "financial_markets", "limit": str(limit)}
    )
    items = []
    for entry in data.get("feed", []) or []:
        title = entry.get("title")
        if not title:
            continue
        published = entry.get("time_published")  # YYYYMMDDTHHMMSS
        published_at = None
        if published:
            try:
                published_at = datetime.strptime(published, "%Y%m%dT%H%M%S").isoformat()
            except ValueError:
                published_at = None
        tickers = [
            t.get("ticker")
            for t in entry.get("ticker_sentiment", [])
            if isinstance(t, dict) and t.get("ticker")
        ]
        items.append(
            {
                "title": title,
                "url": entry.get("url"),
                "source": entry.get("source") or "Alpha Vantage",
                "publishedAt": published_at,
                "summary": entry.get("summary"),
                "tickers": tickers[:3],
            }
        )
    return items
