import math

from app.services.levels import compute_levels


def make_bars(prices, spread=1.0, volume=1_000_000):
    bars = []
    for i, close in enumerate(prices):
        bars.append(
            {
                "t": 1_700_000_000 + i * 86400,
                "dt": f"2026-01-{(i % 28) + 1:02d}T00:00Z",
                "o": close,
                "h": close + spread,
                "l": close - spread,
                "c": close,
                "v": volume,
            }
        )
    return bars


def wave_bars():
    prices = []
    for i in range(140):
        base = 100 + math.sin(i / 4) * 8
        prices.append(round(base, 2))
    return make_bars(prices, spread=1.2)


def test_returns_two_supports_and_two_resistances():
    bars = wave_bars()
    result = compute_levels(bars, method="structure")
    assert len(result["supports"]) == 2
    assert len(result["resistances"]) == 2
    assert result["price"] == bars[-1]["c"]


def test_levels_are_on_the_correct_side_and_sorted():
    result = compute_levels(wave_bars())
    price = result["price"]
    s1, s2 = [l["price"] for l in result["supports"]]
    r1, r2 = [l["price"] for l in result["resistances"]]
    assert s2 < s1 < price < r1 < r2
    for level in result["supports"] + result["resistances"]:
        assert level["zoneLow"] < level["price"] < level["zoneHigh"]
        assert level["distancePct"] < 0 if level["price"] < price else level["distancePct"] > 0


def test_pivot_method_uses_classic_formula():
    bars = make_bars([98, 99, 100, 101, 102, 103, 103.5, 104, 104.2, 104])
    bars[-1].update({"h": 110, "l": 100, "c": 104})
    result = compute_levels(bars, method="pivot")
    assert result["method"] == "pivot"
    assert len(result["supports"]) + len(result["resistances"]) >= 2
    assert all(l["source"] == "pivot" for l in result["supports"] + result["resistances"])


def test_short_history_falls_back_without_crashing():
    result = compute_levels(make_bars([100, 101, 102]), method="structure")
    assert result["fallback"] is True
    assert result["supports"] == []
    assert result["resistances"] == []


def test_flat_history_still_returns_four_levels():
    result = compute_levels(make_bars([100] * 80, spread=0.5))
    assert len(result["supports"]) == 2
    assert len(result["resistances"]) == 2
    price = result["price"]
    assert all(l["price"] < price for l in result["supports"])
    assert all(l["price"] > price for l in result["resistances"])
