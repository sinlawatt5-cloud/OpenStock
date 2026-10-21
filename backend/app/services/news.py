"""News feed: Finnhub company/general news, Yahoo and Alpha Vantage fallbacks."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any

from ..cache import get_cache
from ..db import get_db
from ..providers import ProviderError, alphavantage, finnhub, llm, yahoo
from .common import with_meta

logger = logging.getLogger("openstock.news")

NEWS_TTL = 900
DEFAULT_FOCUS = ["AAPL", "NVDA", "TSLA"]
_MARKET_WORDS = re.compile(
    r"(stock|market|fed|rate|earnings|inflation|oil|gold|bitcoin|dollar|bond|tariff|"
    r"s&p|nasdaq|dow|chip|semiconductor|merger|acquisition|ipo|treasury|investor|"
    r"shares|nasdaq|wall street|economy|gdp|jobless|payroll|ecb|boj)",
    re.IGNORECASE,
)


def _normalize_title(title: str) -> str:
    return re.sub(r"\s+", " ", title.strip().lower())


def _dedupe(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out = []
    for item in items:
        key = _normalize_title(item.get("title", ""))
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def _focus_from_movers() -> list[str]:
    cache = get_cache()
    symbols: list[str] = []
    for key in ("market:movers:gainers", "market:movers:losers", "market:movers:actives"):
        payload = cache.peek(key)
        if not payload:
            continue
        for row in (payload.get("rows") or [])[:2]:
            if row.get("symbol") and row["symbol"] not in symbols:
                symbols.append(row["symbol"])
    return symbols[:4] or DEFAULT_FOCUS


async def _load_feed(focus: tuple[str, ...], scope: str = "market") -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    provider = "finnhub"

    if finnhub.configured():
        if scope != "company":
            try:
                market_items = await finnhub.market_news(limit=80)
                items.extend(
                    [i for i in market_items if i.get("tickers") or _MARKET_WORDS.search(i.get("title", ""))]
                )
            except ProviderError as exc:
                logger.info("finnhub market news failed: %s", exc)
        for symbol in focus[:4]:
            try:
                items.extend(await finnhub.company_news(symbol, days=5, limit=6))
            except ProviderError as exc:
                logger.info("finnhub company news failed for %s: %s", symbol, exc)

    if not items:
        provider = "yfinance"
        for symbol in focus[:3] or DEFAULT_FOCUS:
            items.extend(await yahoo.ticker_news(symbol))

    if scope == "company":
        focus_set = set(focus)
        items = [
            item
            for item in items
            if not item.get("tickers") or focus_set.intersection(item.get("tickers", []))
        ]

    if not items and scope != "company" and alphavantage.configured():
        provider = "alphavantage"
        try:
            items.extend(await alphavantage.news(limit=40))
        except ProviderError as exc:
            logger.info("alphavantage news failed: %s", exc)

    items = _dedupe([i for i in items if i.get("title")])
    items.sort(key=lambda i: i.get("publishedAt") or "", reverse=True)
    if scope == "company" and focus:
        record = get_db().get_symbol(focus[0]) or {}
        tokens = {focus[0].lower()}
        for word in re.split(r"[^A-Za-z0-9]+", record.get("name", "")):
            lower = word.lower()
            if len(lower) >= 4 and lower not in {
                "inc", "corp", "corporation", "company", "holdings", "group",
                "technologies", "platforms", "class", "the", "limited", "plc",
            }:
                tokens.add(lower)

        def relevance(item: dict[str, Any]) -> int:
            title = item.get("title", "").lower()
            return 0 if any(token in title for token in tokens) else 1

        items.sort(key=relevance)

    merged = items[:24]
    for item in merged:
        item.setdefault("tickers", [])
        item.setdefault("source", provider)
    return {"items": merged, "focus": list(focus), "provider": provider}


async def get_news(
    symbols: list[str] | None = None, limit: int = 12, scope: str = "market"
) -> dict[str, Any]:
    scope = scope if scope in {"market", "company"} else "market"
    focus = tuple(
        dict.fromkeys([s.strip().upper() for s in (symbols or []) if s.strip()])
    ) or tuple(_focus_from_movers())
    key = f"news:feed:{scope}:" + ",".join(focus)
    cache = get_cache()
    payload, meta = await cache.get_or_load(
        key, NEWS_TTL, lambda: _load_feed(focus, scope)
    )
    return with_meta(
        {
            "items": payload["items"][: max(1, min(limit, 24))],
            "focus": payload["focus"],
        },
        meta,
        payload.get("provider", "finnhub"),
    )


async def get_summary(symbols: list[str] | None = None, scope: str = "market") -> dict[str, Any]:
    feed = await get_news(symbols, limit=18, scope=scope)
    items = feed["items"]
    result = await llm.summarize(items, get_db())
    sources = [
        {
            "title": item.get("title"),
            "source": item.get("source"),
            "url": item.get("url"),
            "publishedAt": item.get("publishedAt"),
            "tickers": item.get("tickers", []),
        }
        for item in items[:6]
    ]
    provider = result["provider"]
    return {
        "status": "ready" if provider != "rules" else "fallback",
        "text": result["text"],
        "provider": provider,
        "model": result["model"],
        "cached": result.get("cached", False),
        "sources": sources,
        "stale": feed.get("stale", False),
        "asOf": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
