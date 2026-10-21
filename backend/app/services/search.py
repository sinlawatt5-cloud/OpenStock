"""Local-first symbol search."""

from __future__ import annotations

import logging

from ..cache import get_cache
from ..db import get_db
from ..providers import ProviderError, yahoo

logger = logging.getLogger("openstock.search")


async def search_symbols(query: str, limit: int = 10) -> dict:
    query = query.strip()
    if not query:
        return {"query": query, "results": [], "source": "local"}

    db = get_db()
    local = db.search_symbols(query, limit)
    results = [
        {
            "symbol": row["symbol"],
            "name": row["name"],
            "nameTh": row["name_th"],
            "exchange": row["exchange"],
            "sector": row["sector"],
            "source": "local",
        }
        for row in local
    ]

    source = "local"
    if len(results) < min(limit, 6):
        cache = get_cache()

        async def load() -> dict:
            try:
                rows = await yahoo.search(query, limit=limit)
            except ProviderError:
                return {"items": []}
            return {"items": rows}

        payload, _meta = await cache.get_or_load(
            f"search:{query.lower()}", 3600, load
        )
        known = {r["symbol"] for r in results}
        for row in payload["items"]:
            if row["symbol"] in known:
                continue
            results.append(
                {
                    "symbol": row["symbol"],
                    "name": row.get("name") or row["symbol"],
                    "nameTh": None,
                    "exchange": row.get("exchange"),
                    "sector": row.get("sector"),
                    "source": "yahoo",
                }
            )
            known.add(row["symbol"])
        if payload["items"]:
            source = "local+yahoo" if local else "yahoo"

    return {"query": query, "results": results[:limit], "source": source}
