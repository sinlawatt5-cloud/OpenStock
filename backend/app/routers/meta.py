from datetime import datetime, timezone

from fastapi import APIRouter, Query

from ..cache import get_cache
from ..config import get_settings
from ..data.universe import BREADTH_UNIVERSE
from ..db import get_db
from ..providers import alphavantage, finnhub, llm
from ..services.catalog import get_catalog
from ..services.flows import HISTORY_KEY
from ..services.overview import BREADTH_KEY, OVERVIEW_KEY
from ..services.search import search_symbols

router = APIRouter(tags=["meta"])


@router.get("/health")
async def health() -> dict:
    settings = get_settings()
    db = get_db()
    cache = get_cache()
    return {
        "status": "ok",
        "service": "OpenStock API",
        "serverTime": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "mode": "fixtures" if settings.fixtures_mode else "live",
        "providers": {
            "yahoo": {"configured": True},
            "finnhub": {"configured": finnhub.configured()},
            "alphavantage": {"configured": alphavantage.configured()},
            "gemini": {"configured": llm.configured()["gemini"]},
            "openrouter": {"configured": llm.configured()["openrouter"]},
        },
        "models": {
            "gemini": settings.gemini_model,
            "openrouter": settings.openrouter_model,
        },
        "budget": {
            "alphavantageUsedToday": db.budget_used("alphavantage"),
            "alphavantageDailyCap": settings.alphavantage_daily_cap,
            "llmUsedToday": db.budget_used("llm"),
            "llmDailyCap": settings.llm_daily_cap,
        },
        "cache": {
            "overviewAgeSeconds": cache.db.cache_age(OVERVIEW_KEY),
            "flowsAgeSeconds": cache.db.cache_age(HISTORY_KEY),
            "breadthAgeSeconds": cache.db.cache_age(BREADTH_KEY),
        },
        "symbolCount": db.symbol_count(),
        "breadthUniverseSize": len(BREADTH_UNIVERSE),
    }


@router.get("/catalog")
async def catalog() -> dict:
    return get_catalog()


@router.get("/symbols")
async def symbols(limit: int = Query(30, ge=1, le=30)) -> dict:
    rows = get_db().list_symbols(limit)
    return {
        "items": [
            {
                "symbol": r["symbol"],
                "name": r["name"],
                "nameTh": r["name_th"],
                "exchange": r["exchange"],
                "sector": r["sector"],
                "industry": r["industry"],
            }
            for r in rows
        ]
    }


@router.get("/search")
async def search(q: str = Query("", min_length=0, max_length=40)) -> dict:
    return await search_symbols(q)
