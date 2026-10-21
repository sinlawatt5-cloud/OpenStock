"""yfinance (Yahoo Finance) provider.

All calls are blocking, so they run in a worker thread. Responses are normalized
into plain dicts that can be cached as JSON.
"""

from __future__ import annotations

import asyncio
import logging
import math
from datetime import datetime, timezone
from typing import Any

import yfinance as yf

from . import ProviderError

logger = logging.getLogger("openstock.yahoo")


def _num(value: Any) -> float | None:
    try:
        if value is None:
            return None
        f = float(value)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (TypeError, ValueError):
        return None


def _bars_from_frame(frame: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if frame is None or getattr(frame, "empty", True):
        return rows
    columns = {str(c).lower(): c for c in frame.columns}
    for idx, row in frame.iterrows():
        close = _num(row.get(columns.get("close")))
        if close is None:
            continue
        ts = idx.to_pydatetime()
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        rows.append(
            {
                "t": int(ts.timestamp()),
                "dt": ts.astimezone(timezone.utc).isoformat(timespec="minutes"),
                "o": _num(row.get(columns.get("open"))) or close,
                "h": _num(row.get(columns.get("high"))) or close,
                "l": _num(row.get(columns.get("low"))) or close,
                "c": close,
                "v": _num(row.get(columns.get("volume"))) or 0,
            }
        )
    return rows


def _parse_download(df: Any, requested: list[str]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    if df is None or getattr(df, "empty", True):
        return out
    try:
        columns = df.columns
        is_multi = getattr(columns, "nlevels", 1) > 1
    except Exception:
        is_multi = False
    if is_multi:
        level0 = list(dict.fromkeys(columns.get_level_values(0)))
        for ticker in level0:
            try:
                sub = df[ticker]
            except Exception:
                continue
            rows = _bars_from_frame(sub)
            if rows:
                out[str(ticker)] = rows
    else:
        rows = _bars_from_frame(df)
        if rows and len(requested) == 1:
            out[requested[0]] = rows
    return out


def _download_sync(
    symbols: list[str], period: str, interval: str
) -> dict[str, list[dict[str, Any]]]:
    df = yf.download(
        symbols,
        period=period,
        interval=interval,
        group_by="ticker",
        auto_adjust=False,
        actions=False,
        progress=False,
        threads=len(symbols) > 1,
        timeout=20,
    )
    return _parse_download(df, symbols)


async def history(
    symbols: list[str], period: str = "1y", interval: str = "1d"
) -> dict[str, list[dict[str, Any]]]:
    symbols = [s for s in symbols if s]
    if not symbols:
        return {}
    try:
        data = await asyncio.wait_for(
            asyncio.to_thread(_download_sync, symbols, period, interval), timeout=45
        )
    except Exception as exc:  # yfinance raises many low-level errors
        raise ProviderError(f"yahoo history failed: {exc}") from exc
    if not data:
        raise ProviderError("yahoo history returned no data")
    return data


def _screen_sync(name: str, count: int) -> list[dict[str, Any]]:
    result = yf.screen(name, count=count)
    quotes = result.get("quotes", []) if isinstance(result, dict) else []
    out = []
    for q in quotes:
        symbol = q.get("symbol")
        price = _num(q.get("regularMarketPrice"))
        if not symbol or price is None:
            continue
        out.append(
            {
                "symbol": symbol,
                "name": q.get("longName") or q.get("shortName") or symbol,
                "price": price,
                "change": _num(q.get("regularMarketChange")),
                "changePct": _num(q.get("regularMarketChangePercent")),
                "volume": _num(q.get("regularMarketVolume")),
                "exchange": q.get("fullExchangeName") or q.get("exchange"),
                "logo": q.get("logoUrl"),
            }
        )
    return out


async def screen(name: str, count: int = 25) -> list[dict[str, Any]]:
    try:
        rows = await asyncio.wait_for(asyncio.to_thread(_screen_sync, name, count), timeout=40)
    except Exception as exc:
        raise ProviderError(f"yahoo screen failed: {exc}") from exc
    if not rows:
        raise ProviderError(f"yahoo screen {name} empty")
    return rows


def _search_sync(query: str, limit: int) -> list[dict[str, Any]]:
    result = yf.Search(query, max_results=limit)
    out = []
    for q in getattr(result, "quotes", []) or []:
        symbol = q.get("symbol")
        if not symbol or q.get("quoteType") not in {"EQUITY", "ETF", "MUTUALFUND"}:
            continue
        if any(ch in symbol for ch in "=^."):
            continue
        out.append(
            {
                "symbol": symbol,
                "name": q.get("longname") or q.get("shortname") or symbol,
                "exchange": q.get("exchDisp") or q.get("exchange"),
                "type": q.get("quoteType"),
                "sector": q.get("sector"),
                "industry": q.get("industry"),
            }
        )
    return out


async def search(query: str, limit: int = 8) -> list[dict[str, Any]]:
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(_search_sync, query, limit), timeout=25
        )
    except Exception as exc:
        raise ProviderError(f"yahoo search failed: {exc}") from exc


def _info_sync(symbol: str) -> dict[str, Any]:
    ticker = yf.Ticker(symbol)
    return ticker.info or {}


def _dividend_yield(info: dict[str, Any]) -> float | None:
    """Return dividend yield in percent, tolerating Yahoo's mixed units."""
    rate = _num(info.get("trailingAnnualDividendRate"))
    price = _num(info.get("regularMarketPrice")) or _num(info.get("previousClose"))
    if rate is not None and price:
        return round(rate / price * 100, 3)
    trailing = _num(info.get("trailingAnnualDividendYield"))
    if trailing is not None and trailing < 0.2:
        return round(trailing * 100, 3)
    plain = _num(info.get("dividendYield"))
    return round(plain, 3) if plain is not None else None


async def profile(symbol: str) -> dict[str, Any]:
    try:
        info = await asyncio.wait_for(asyncio.to_thread(_info_sync, symbol), timeout=30)
    except Exception as exc:
        raise ProviderError(f"yahoo profile failed: {exc}") from exc
    if not info or not info.get("symbol"):
        raise ProviderError("yahoo profile empty")
    return {
        "symbol": info.get("symbol", symbol),
        "name": info.get("longName") or info.get("shortName") or symbol,
        "exchange": info.get("fullExchangeName") or info.get("exchange"),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "logo": info.get("logoUrl"),
        "website": info.get("website"),
        "summary": info.get("longBusinessSummary"),
        "employees": info.get("fullTimeEmployees"),
        "marketCap": _num(info.get("marketCap")),
        "peTrailing": _num(info.get("trailingPE")),
        "peForward": _num(info.get("forwardPE")),
        "week52High": _num(info.get("fiftyTwoWeekHigh")),
        "week52Low": _num(info.get("fiftyTwoWeekLow")),
        "avgVolume": _num(info.get("averageVolume")),
        "fiftyDayAverage": _num(info.get("fiftyDayAverage")),
        "dividendYield": _dividend_yield(info),
        "beta": _num(info.get("beta")),
        "currency": info.get("currency", "USD"),
    }


def _news_sync(symbol: str) -> list[dict[str, Any]]:
    raw = yf.Ticker(symbol).news or []
    items = []
    for entry in raw:
        content = entry.get("content") if isinstance(entry, dict) else None
        if isinstance(content, dict):
            title = content.get("title")
            url = (content.get("canonicalUrl") or {}).get("url") or (
                content.get("clickThroughUrl") or {}
            ).get("url")
            provider = (content.get("provider") or {}).get("displayName")
            published = content.get("pubDate") or content.get("displayTime")
            summary = content.get("summary") or content.get("description")
            tickers = [
                t.get("symbol")
                for t in (content.get("relatedTickers") or [])
                if isinstance(t, dict)
            ]
        else:
            title = entry.get("title")
            url = entry.get("link")
            provider = entry.get("publisher")
            published = entry.get("providerPublishTime")
            summary = None
            tickers = []
        if not title:
            continue
        if isinstance(published, (int, float)):
            published = datetime.fromtimestamp(published, timezone.utc).isoformat()
        items.append(
            {
                "title": title,
                "url": url,
                "source": provider or "Yahoo Finance",
                "publishedAt": published,
                "summary": summary,
                "tickers": tickers or [symbol],
            }
        )
    return items


async def ticker_news(symbol: str) -> list[dict[str, Any]]:
    try:
        return await asyncio.wait_for(asyncio.to_thread(_news_sync, symbol), timeout=25)
    except Exception as exc:
        logger.info("yahoo news unavailable for %s: %s", symbol, exc)
        return []
