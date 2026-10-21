from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .cache import get_cache
from .config import get_settings
from .db import get_db
from .providers import ProviderError
from .routers import flows, market, meta, news, symbol
from .services.flows import HISTORY_KEY, HISTORY_TTL, _load_history
from .services.movers import TTL as MOVERS_TTL
from .services.movers import _load_list
from .services.overview import OVERVIEW_KEY, OVERVIEW_TTL, _load_overview, get_breadth

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("openstock")


async def _warm_cache() -> None:
    """Warm the expensive caches once, sequentially, to stay inside free quotas."""
    cache = get_cache()
    try:
        await get_breadth()
    except Exception as exc:  # pragma: no cover - upstream dependent
        logger.info("breadth warm-up skipped: %s", exc)
    tasks = [
        (OVERVIEW_KEY, OVERVIEW_TTL, _load_overview),
        (HISTORY_KEY, HISTORY_TTL, _load_history),
        ("market:movers:gainers", MOVERS_TTL, lambda: _load_list("gainers")),
        ("market:movers:losers", MOVERS_TTL, lambda: _load_list("losers")),
        ("market:movers:actives", MOVERS_TTL, lambda: _load_list("actives")),
    ]
    for key, ttl, loader in tasks:
        if cache.db.cache_age(key) is not None and cache.db.cache_age(key) < ttl:  # type: ignore[operator]
            continue
        cache.prefetch(key, ttl, loader)
        await asyncio.sleep(1.0)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    db = get_db()
    if settings.fixtures_mode:
        from . import fixtures

        fixtures.seed(db)
    logger.info(
        "OpenStock API starting (mode=%s, finnhub=%s, llm=%s)",
        "fixtures" if settings.fixtures_mode else "live",
        bool(settings.finnhub_api_key),
        bool(settings.gemini_api_key or settings.openrouter_api_key),
    )
    if settings.openstock_enable_background_prefetch and not settings.fixtures_mode:
        asyncio.create_task(_warm_cache())
    yield
    logger.info("OpenStock API stopped")


app = FastAPI(
    title="OpenStock API",
    description="Free-tier market dashboard API for OpenStock",
    version="0.1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
    ],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

for router in (market.router, flows.router, news.router, symbol.router, meta.router):
    app.include_router(router, prefix="/api")


@app.exception_handler(ProviderError)
async def provider_error_handler(request: Request, exc: ProviderError) -> JSONResponse:
    logger.warning("provider error on %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=503,
        content={
            "detail": "แหล่งข้อมูลภายนอกไม่ตอบสนองในขณะนี้",
            "reason": str(exc),
        },
    )


@app.get("/api")
async def root() -> dict:
    return {"service": "OpenStock API", "docs": "/api/docs", "health": "/api/health"}
