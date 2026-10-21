from typing import Literal

from fastapi import APIRouter, Query

from ..services.movers import get_movers
from ..services.overview import get_overview

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/overview")
async def overview() -> dict:
    return await get_overview()


@router.get("/movers")
async def movers(
    list: Literal["gainers", "losers", "actives"] = Query("gainers"),
    limit: int = Query(5, ge=1, le=10),
) -> dict:
    return await get_movers(list, limit)
