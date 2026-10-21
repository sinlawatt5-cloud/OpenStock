from __future__ import annotations

from typing import Any

from ..cache import CacheMeta


def with_meta(payload: dict[str, Any], meta: CacheMeta, provider: str) -> dict[str, Any]:
    return {
        **payload,
        "stale": meta.stale,
        "asOf": meta.as_of,
        "ageSeconds": meta.age_seconds,
        "provider": provider,
    }


def pct_change(current: float | None, previous: float | None) -> float | None:
    if current is None or previous in (None, 0):
        return None
    return round((current / previous - 1) * 100, 2)


def round_or_none(value: float | None, digits: int = 2) -> float | None:
    return None if value is None else round(value, digits)
