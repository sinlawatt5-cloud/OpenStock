"""Flow board: percentage moves of ETF groups used as a money-flow proxy."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from ..cache import get_cache
from ..data.universe import BENCHMARK, GROUP_META, GROUPS, all_etf_symbols
from ..providers import ProviderError, yahoo
from .common import with_meta

logger = logging.getLogger("openstock.flows")

HISTORY_KEY = "flows:history"
HISTORY_TTL = 600
VALID_RANGES = {"1d", "1w", "1mo", "3mo", "ytd"}
VALID_GROUPS = {meta["key"] for meta in GROUP_META} | {"all"}


async def _load_history() -> dict[str, Any]:
    return await yahoo.history(all_etf_symbols(), period="1y", interval="1d")


def _base_index(bars: list[dict[str, Any]], range_key: str) -> int | None:
    n = len(bars)
    if n < 2:
        return None
    if range_key == "1d":
        return n - 2
    if range_key == "1w":
        return max(0, n - 6)
    if range_key == "1mo":
        return max(0, n - 22)
    if range_key == "3mo":
        return max(0, n - 64)
    if range_key == "ytd":
        last_year = bars[-1]["dt"][:4]
        for i in range(n - 1, -1, -1):
            if bars[i]["dt"][:4] != last_year:
                return i
        return 0
    return n - 2


def _row_for(
    item: dict[str, Any], bars: list[dict[str, Any]], range_key: str
) -> dict[str, Any] | None:
    if len(bars) < 2:
        return None
    base_i = _base_index(bars, range_key)
    if base_i is None:
        return None
    base = bars[base_i]["c"]
    last = bars[-1]
    if not base:
        return None
    pct = (last["c"] / base - 1) * 100
    dollar_volume = (last["c"] or 0) * (last.get("v") or 0)
    return {
        "symbol": item["symbol"],
        "name": item.get("name", item["symbol"]),
        "nameTh": item.get("name_th", item["symbol"]),
        "price": round(last["c"], 2),
        "change": round(last["c"] - base, 2),
        "pct": round(pct, 2),
        "dollarVolume": round(dollar_volume, 0),
        "benchmark": False,
    }


def build_rows(
    history: dict[str, list[dict[str, Any]]], group: str, range_key: str
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if group == "all":
        items = [item for key in GROUPS for item in GROUPS[key]]
    else:
        items = list(GROUPS.get(group, []))

    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in items:
        if item["symbol"] in seen or item["symbol"] == BENCHMARK["symbol"]:
            continue
        seen.add(item["symbol"])
        row = _row_for(item, history.get(item["symbol"], []), range_key)
        if row:
            rows.append(row)

    bench = _row_for(
        {"symbol": BENCHMARK["symbol"], "name": BENCHMARK["name"], "name_th": BENCHMARK["name_th"]},
        history.get(BENCHMARK["symbol"], []),
        range_key,
    )
    if bench:
        bench["benchmark"] = True
        rows.append(bench)

    rows.sort(key=lambda r: r["pct"], reverse=True)
    positive = [r for r in rows if not r["benchmark"] and r["pct"] > 0]
    negative = [r for r in rows if not r["benchmark"] and r["pct"] < 0]
    tracked = sum(1 for r in rows if not r["benchmark"])
    summary = {
        "inflow": len(positive),
        "outflow": len(negative),
        "total": tracked,
        "benchmarkPct": bench["pct"] if bench else None,
        "label": _signal_label(len(positive), len(positive) + len(negative)),
    }
    return rows, summary


def _signal_label(positive: int, total: int) -> str:
    if not total:
        return "ยังไม่มีข้อมูลเพียงพอ"
    ratio = positive / total
    if ratio >= 0.75:
        return "แรงซื้อกระจายตัวกว้าง"
    if ratio >= 0.5:
        return "แรงซื้อเริ่มได้เปรียบ"
    if ratio >= 0.25:
        return "แรงขายเริ่มได้เปรียบ"
    return "แรงขายกระจายตัวกว้าง"


async def get_flows(group: str, range_key: str, mode: str = "all") -> dict[str, Any]:
    cache = get_cache()
    group = group if group in VALID_GROUPS else "broad"
    range_key = range_key if range_key in VALID_RANGES else "1d"
    mode = mode if mode in {"all", "inflow", "outflow"} else "all"

    try:
        history, meta = await cache.get_or_load(HISTORY_KEY, HISTORY_TTL, _load_history)
        provider = "yfinance"
    except ProviderError:
        stale = cache.peek(HISTORY_KEY)
        if not stale:
            raise
        from ..cache import CacheMeta

        history = stale
        meta = CacheMeta(True, datetime.now(timezone.utc).isoformat(timespec="seconds"), 0)
        provider = "cache"

    rows, summary = build_rows(history, group, range_key)
    max_abs = max((abs(r["pct"]) for r in rows), default=1) or 1
    for row in rows:
        row["flowScore"] = round(abs(row["pct"]) / max_abs * 100, 1)

    if mode == "inflow":
        rows = [r for r in rows if r["pct"] > 0]
    elif mode == "outflow":
        rows = [r for r in rows if r["pct"] < 0]
        rows.sort(key=lambda r: r["pct"])

    meta_info = next((m for m in GROUP_META if m["key"] == group), None)
    description = (
        meta_info["description"] if meta_info else "ทุกกลุ่มที่ติดตาม — เทียบเป็นเปอร์เซ็นต์ในช่วงเวลาที่เลือก"
    )
    return with_meta(
        {
            "group": group,
            "range": range_key,
            "mode": mode,
            "description": description,
            "rows": rows,
            "summary": summary,
        },
        meta,
        provider,
    )
