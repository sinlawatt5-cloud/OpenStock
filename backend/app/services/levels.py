"""Support / resistance levels.

Primary method clusters swing pivots (2 nearest supports + 2 nearest resistances).
Fallback is the classic pivot-point formula from the latest bar.
"""

from __future__ import annotations

from typing import Any

DEFAULT_K = 5
ATR_PERIOD = 14


def _atr(bars: list[dict[str, Any]], period: int = ATR_PERIOD) -> float:
    if not bars:
        return 0.0
    ranges = []
    for i, bar in enumerate(bars):
        high, low = bar["h"], bar["l"]
        prev_close = bars[i - 1]["c"] if i > 0 else None
        if prev_close is None:
            ranges.append(high - low)
        else:
            ranges.append(max(high - low, abs(high - prev_close), abs(low - prev_close)))
    window = ranges[-period:] if len(ranges) > period else ranges
    return sum(window) / len(window) if window else 0.0


def _classic_pivots(bar: dict[str, Any]) -> dict[str, float]:
    p = (bar["h"] + bar["l"] + bar["c"]) / 3
    return {
        "pivot": p,
        "s1": 2 * p - bar["h"],
        "s2": p - (bar["h"] - bar["l"]),
        "r1": 2 * p - bar["l"],
        "r2": p + (bar["h"] - bar["l"]),
    }


def _pivots(bars: list[dict[str, Any]], k: int) -> list[dict[str, Any]]:
    pivots: list[dict[str, Any]] = []
    for i in range(k, len(bars) - k):
        window = bars[i - k : i + k + 1]
        high = bars[i]["h"]
        low = bars[i]["l"]
        if high >= max(b["h"] for b in window):
            pivots.append({"price": high, "index": i, "kind": "high", "volume": bars[i].get("v") or 0})
        if low <= min(b["l"] for b in window):
            pivots.append({"price": low, "index": i, "kind": "low", "volume": bars[i].get("v") or 0})
    return pivots


def _cluster(pivots: list[dict[str, Any]], atr: float, bars_len: int) -> list[dict[str, Any]]:
    if not pivots:
        return []
    tolerance = max(atr * 0.5, 1e-6)
    ordered = sorted(pivots, key=lambda p: p["price"])
    clusters: list[list[dict[str, Any]]] = []
    for pivot in ordered:
        if clusters and abs(pivot["price"] - clusters[-1][-1]["price"]) <= tolerance:
            clusters[-1].append(pivot)
        else:
            clusters.append([pivot])

    levels = []
    for cluster in clusters:
        touches = len(cluster)
        price = sum(p["price"] for p in cluster) / touches
        latest_index = max(p["index"] for p in cluster)
        recency = latest_index / max(bars_len - 1, 1)
        volume_weight = min(1.0, sum(p.get("volume", 0) for p in cluster) / (touches * 1e6 + 1))
        strength = min(1.0, 0.25 + 0.16 * touches + 0.25 * recency + 0.1 * volume_weight)
        levels.append(
            {
                "price": price,
                "touches": touches,
                "strength": round(strength, 2),
                "zoneLow": price - atr * 0.25,
                "zoneHigh": price + atr * 0.25,
            }
        )
    return levels


def _decorate(level: dict[str, Any], price: float) -> dict[str, Any]:
    return {
        "price": round(level["price"], 2),
        "zoneLow": round(level["zoneLow"], 2),
        "zoneHigh": round(level["zoneHigh"], 2),
        "touches": level.get("touches", 1),
        "strength": level.get("strength", 0.4),
        "distancePct": round((level["price"] / price - 1) * 100, 2),
        "source": level.get("source", "structure"),
    }


def _extras(
    bars: list[dict[str, Any]], atr: float, existing: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Classic pivot levels plus range extremes, nearest-to-price first."""
    extras: list[dict[str, Any]] = []
    piv = _classic_pivots(bars[-1])
    for key, strength in (("s1", 0.34), ("s2", 0.3), ("r1", 0.34), ("r2", 0.3)):
        value = piv[key]
        if value <= 0:
            continue
        if any(abs(value - level["price"]) < atr * 0.15 for level in existing + extras):
            continue
        extras.append(
            {
                "price": value,
                "zoneLow": value - atr * 0.2,
                "zoneHigh": value + atr * 0.2,
                "touches": 1,
                "strength": strength,
                "source": "pivot",
            }
        )
    low = min(b["l"] for b in bars[-120:])
    high = max(b["h"] for b in bars[-120:])
    for value in (low, high):
        if any(abs(value - level["price"]) < atr * 0.15 for level in existing + extras):
            continue
        extras.append(
            {
                "price": value,
                "zoneLow": value - atr * 0.2,
                "zoneHigh": value + atr * 0.2,
                "touches": 1,
                "strength": 0.25,
                "source": "range",
            }
        )
    return extras


def _fill_side(
    levels: list[dict[str, Any]],
    extras: list[dict[str, Any]],
    price: float,
    side: str,
    atr: float,
) -> list[dict[str, Any]]:
    filled = list(levels)[:2]
    candidates = sorted(
        [e for e in extras if (e["price"] < price if side == "support" else e["price"] > price)],
        key=lambda e: abs(e["price"] - price),
    )
    for candidate in candidates:
        if len(filled) >= 2:
            break
        if any(abs(candidate["price"] - l["price"]) < atr * 0.15 for l in filled):
            continue
        filled.append(candidate)
    if side == "support":
        filled.sort(key=lambda l: l["price"], reverse=True)
    else:
        filled.sort(key=lambda l: l["price"])
    return filled[:2]


def compute_levels(
    bars: list[dict[str, Any]], method: str = "structure", k: int = DEFAULT_K
) -> dict[str, Any]:
    if len(bars) < 6:
        return {
            "supports": [],
            "resistances": [],
            "method": method,
            "atr": 0.0,
            "fallback": True,
            "price": bars[-1]["c"] if bars else None,
        }

    price = bars[-1]["c"]
    atr = _atr(bars) or (price * 0.01)

    if method == "pivot":
        piv = _classic_pivots(bars[-1])
        candidates = [
            {"price": piv["s2"], "zoneLow": piv["s2"] - atr * 0.2, "zoneHigh": piv["s2"] + atr * 0.2, "touches": 1, "strength": 0.35, "source": "pivot"},
            {"price": piv["s1"], "zoneLow": piv["s1"] - atr * 0.2, "zoneHigh": piv["s1"] + atr * 0.2, "touches": 1, "strength": 0.4, "source": "pivot"},
            {"price": piv["r1"], "zoneLow": piv["r1"] - atr * 0.2, "zoneHigh": piv["r1"] + atr * 0.2, "touches": 1, "strength": 0.4, "source": "pivot"},
            {"price": piv["r2"], "zoneLow": piv["r2"] - atr * 0.2, "zoneHigh": piv["r2"] + atr * 0.2, "touches": 1, "strength": 0.35, "source": "pivot"},
        ]
        supports = sorted([c for c in candidates if c["price"] < price], key=lambda c: c["price"], reverse=True)[:2]
        resistances = sorted([c for c in candidates if c["price"] > price], key=lambda c: c["price"])[:2]
        return {
            "supports": [_decorate(c, price) for c in supports],
            "resistances": [_decorate(c, price) for c in resistances],
            "method": "pivot",
            "atr": round(atr, 2),
            "fallback": False,
            "price": round(price, 2),
        }

    pivots = _pivots(bars, k)
    levels = _cluster(pivots, atr, len(bars))
    supports = sorted([l for l in levels if l["price"] < price], key=lambda l: l["price"], reverse=True)[:2]
    resistances = sorted([l for l in levels if l["price"] > price], key=lambda l: l["price"])[:2]

    fallback = len(supports) < 2 or len(resistances) < 2
    if fallback:
        extras = _extras(bars, atr, supports + resistances)
        supports = _fill_side(supports, extras, price, "support", atr)
        resistances = _fill_side(resistances, extras, price, "resistance", atr)

    return {
        "supports": [_decorate(l, price) for l in supports],
        "resistances": [_decorate(l, price) for l in resistances],
        "method": "structure",
        "atr": round(atr, 2),
        "fallback": fallback,
        "price": round(price, 2),
    }
