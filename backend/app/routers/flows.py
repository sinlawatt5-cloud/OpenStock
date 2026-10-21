from typing import Literal

from fastapi import APIRouter, Query

from ..services.flows import get_flows

router = APIRouter(tags=["flows"])


@router.get("/flows")
async def flows(
    group: Literal["broad", "sectors", "industries", "themes", "all"] = Query("sectors"),
    range: Literal["1d", "1w", "1mo", "3mo", "ytd"] = Query("1d"),
    mode: Literal["all", "inflow", "outflow"] = Query("all"),
) -> dict:
    return await get_flows(group, range, mode)
