from typing import Literal

from fastapi import APIRouter, Query

from ..services.symbol import (
    get_history,
    get_levels,
    get_quote,
    get_symbol_page,
)

router = APIRouter(tags=["symbol"])

RangeKey = Literal["1d", "5d", "1mo", "6mo", "1y", "5y"]


@router.get("/quote/{symbol}")
async def quote(symbol: str) -> dict:
    return await get_quote(symbol)


@router.get("/history/{symbol}")
async def history(symbol: str, range: RangeKey = Query("1y")) -> dict:
    return await get_history(symbol, range)


@router.get("/symbol/{symbol}/profile")
async def profile(symbol: str) -> dict:
    return await get_symbol_page(symbol)


@router.get("/symbol/{symbol}/levels")
async def levels(
    symbol: str,
    range: RangeKey = Query("6mo"),
    method: Literal["structure", "pivot"] = Query("structure"),
) -> dict:
    return await get_levels(symbol, range, method)
