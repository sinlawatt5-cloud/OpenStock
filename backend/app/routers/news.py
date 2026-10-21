from typing import Literal

from fastapi import APIRouter, Query

from ..services.news import get_news, get_summary

router = APIRouter(prefix="/news", tags=["news"])


@router.get("")
async def news(
    limit: int = Query(12, ge=1, le=24),
    symbols: str | None = Query(None, description="comma separated tickers"),
    scope: Literal["market", "company"] = Query("market"),
) -> dict:
    focus = [s for s in (symbols or "").split(",") if s.strip()] or None
    return await get_news(focus, limit, scope)


@router.get("/summary")
async def summary(
    symbols: str | None = Query(None, description="comma separated tickers"),
) -> dict:
    focus = [s for s in (symbols or "").split(",") if s.strip()] or None
    return await get_summary(focus)
