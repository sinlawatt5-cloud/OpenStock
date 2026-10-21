"""Top gainers / losers / most active."""

from __future__ import annotations

import logging
from typing import Any

from ..cache import get_cache
from ..data.universe import BREADTH_UNIVERSE
from ..providers import ProviderError, yahoo
from .common import with_meta

logger = logging.getLogger("openstock.movers")

LISTS = {
    "gainers": "day_gainers",
    "losers": "day_losers",
    "actives": "most_actives",
}
TTL = 300


def _clean_rows(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        price = row.get("price")
        change_pct = row.get("changePct")
        if price is None or change_pct is None or price < 3:
            continue
        if (row.get("volume") or 0) < 100_000:
            continue
        if "." in row["symbol"] or "=" in row["symbol"] or "^" in row["symbol"]:
            continue
        out.append(row)
        if len(out) >= limit:
            break
    return out


async def _load_list(list_key: str) -> dict[str, Any]:
    provider = "yfinance"
    try:
        rows = await yahoo.screen(LISTS[list_key], count=40)
    except ProviderError as exc:
        logger.warning("screener %s failed (%s), computing fallback", list_key, exc)
        rows = await _fallback_rows()
        provider = "computed"

    cleaned = _clean_rows(rows, 25)
    if list_key == "losers":
        cleaned.sort(key=lambda r: r.get("changePct") or 0)
    elif list_key == "gainers":
        cleaned.sort(key=lambda r: r.get("changePct") or 0, reverse=True)
    else:
        cleaned.sort(key=lambda r: (r.get("volume") or 0), reverse=True)
    return {"rows": cleaned[:10], "provider": provider}


async def _fallback_rows() -> list[dict[str, Any]]:
    cache = get_cache()
    key = "market:movers:fallback-source"

    async def load() -> dict[str, Any]:
        hist = await yahoo.history(BREADTH_UNIVERSE, period="1mo", interval="1d")
        return hist

    hist, _meta = await cache.get_or_load(key, TTL, load)
    rows = []
    for symbol, bars in hist.items():
        if len(bars) < 2:
            continue
        last, prev = bars[-1], bars[-2]
        if not prev["c"]:
            continue
        rows.append(
            {
                "symbol": symbol,
                "name": symbol,
                "price": round(last["c"], 2),
                "change": round(last["c"] - prev["c"], 2),
                "changePct": round((last["c"] / prev["c"] - 1) * 100, 2),
                "volume": last.get("v") or 0,
            }
        )
    return rows


async def get_movers(list_key: str, limit: int = 5) -> dict[str, Any]:
    key = f"market:movers:{list_key}"
    cache = get_cache()
    payload, meta = await cache.get_or_load(
        key, TTL, lambda: _load_list(list_key)
    )
    rows = payload["rows"][: max(1, min(limit, 10))]
    return with_meta(
        {"list": list_key, "rows": rows},
        meta,
        payload.get("provider", "yfinance"),
    )
