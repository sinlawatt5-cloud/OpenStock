from app.data.universe import GROUPS
from app.services.flows import _base_index, build_rows


def bars_with_pct(pct, days=30, year=2026):
    closes = [100 * (1 + (pct / 100) * i / (days - 1)) for i in range(days)]
    bars = []
    for i, close in enumerate(closes):
        bars.append(
            {
                "t": 1_700_000_000 + i * 86400,
                "dt": f"{year}-01-{(i % 28) + 1:02d}T00:00Z",
                "o": close,
                "h": close * 1.01,
                "l": close * 0.99,
                "c": close,
                "v": 2_000_000,
            }
        )
    return bars


def sector_history():
    history = {}
    for i, item in enumerate(GROUPS["sectors"]):
        history[item["symbol"]] = bars_with_pct(pct=float(i + 1) * 0.5)
    history["SPY"] = bars_with_pct(pct=0.4)
    return history


def test_build_rows_includes_benchmark_and_sorted_desc():
    rows, summary = build_rows(sector_history(), "sectors", "3mo")
    assert len(rows) == len(GROUPS["sectors"]) + 1
    assert [r["pct"] for r in rows] == sorted((r["pct"] for r in rows), reverse=True)
    benchmarks = [r for r in rows if r["benchmark"]]
    assert len(benchmarks) == 1
    assert benchmarks[0]["symbol"] == "SPY"
    assert summary["total"] == len(GROUPS["sectors"])
    assert summary["inflow"] + summary["outflow"] == summary["total"]


def test_one_day_range_uses_previous_close():
    history = {"SPY": bars_with_pct(pct=0.4)}
    rows, _ = build_rows(history, "sectors", "1d")
    assert len(rows) == 1
    bars = history["SPY"]
    expected = (bars[-1]["c"] / bars[-2]["c"] - 1) * 100
    assert abs(rows[0]["pct"] - expected) < 0.01


def test_ytd_uses_last_close_of_previous_year():
    bars = bars_with_pct(pct=10, days=30, year=2025)
    for bar in bars[20:]:
        bar["dt"] = bar["dt"].replace("2025", "2026")
    history = {"SPY": bars}
    rows, _ = build_rows(history, "sectors", "ytd")
    base = bars[19]["c"]
    assert abs(rows[0]["pct"] - (bars[-1]["c"] / base - 1) * 100) < 0.01


def test_base_index_handles_short_series():
    assert _base_index([], "1d") is None
    assert _base_index([{"dt": "2026-01-01T00:00Z", "c": 1}], "1d") is None
    assert _base_index(bars_with_pct(1, days=5), "3mo") == 0


def test_all_group_deduplicates_symbols():
    history = sector_history()
    for key in ("broad", "industries", "themes"):
        for item in GROUPS[key]:
            history.setdefault(item["symbol"], bars_with_pct(pct=1.0))
    rows, _ = build_rows(history, "all", "1w")
    symbols = [r["symbol"] for r in rows]
    assert len(symbols) == len(set(symbols))
