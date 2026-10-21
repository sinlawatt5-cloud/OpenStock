from app.data.universe import GROUPS
from app.services.flows import _base_index, build_risk_signals, build_rows


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


# --- Risk-on 6-signal panel ---


def risk_history(pcts: dict[str, float]) -> dict[str, list]:
    return {symbol: bars_with_pct(pct=pct) for symbol, pct in pcts.items()}


ALL_RISK_ETFS = ["IWM", "RSP", "HYG", "LQD", "EEM", "UUP", "GLD", "SPY"]


def test_risk_signals_positive_when_spreads_favor_risk():
    # Everything up 1%, dollar down 1% -> 6/6 risk-on (all spreads are zero here
    # except dollar, so craft explicit winners instead).
    history = risk_history(
        {"IWM": 2.0, "RSP": 2.0, "HYG": 2.0, "LQD": 1.0, "EEM": 2.0, "UUP": -1.0, "GLD": 0.5, "SPY": 1.0}
    )
    result = build_risk_signals(history, "1w")
    assert result["of"] == 6
    assert result["score"] == 6
    assert all(s["status"] == "positive" for s in result["signals"])


def test_risk_signals_negative_when_spreads_favor_safety():
    history = risk_history(
        {"IWM": 0.5, "RSP": 0.5, "HYG": 0.5, "LQD": 2.0, "EEM": 0.5, "UUP": 1.0, "GLD": 3.0, "SPY": 1.0}
    )
    result = build_risk_signals(history, "1w")
    assert result["score"] == 0
    statuses = {s["id"]: s["status"] for s in result["signals"]}
    assert all(status == "negative" for status in statuses.values())


def test_risk_signals_zero_diff_is_not_positive():
    # IWM == SPY exactly -> signal 1 must not count as positive.
    history = risk_history({"IWM": 1.0, "SPY": 1.0})
    result = build_risk_signals(history, "1mo")
    first = result["signals"][0]
    assert first["id"] == "small_caps_lead"
    assert first["status"] == "negative"


def test_risk_signals_missing_etf_is_unavailable_not_positive():
    history = risk_history({"IWM": 2.0, "SPY": 1.0})  # RSP, LQD, UUP, GLD missing
    result = build_risk_signals(history, "1w")
    statuses = {s["id"]: s["status"] for s in result["signals"]}
    assert statuses["equal_weight_wins"] == "unavailable"
    assert statuses["junk_beats_ig"] == "unavailable"
    assert statuses["dollar_weak"] == "unavailable"
    assert statuses["gold_loses"] == "unavailable"
    assert statuses["small_caps_lead"] == "positive"
    # Unavailable signals must not be counted in the score.
    assert result["score"] == 1
    # EEM missing -> em_wins unavailable too (not guessed either way).
    assert statuses["em_wins"] == "unavailable"


def test_risk_signals_short_series_is_unavailable():
    history = risk_history({"IWM": 2.0, "SPY": 1.0})
    history["IWM"] = history["IWM"][:1]  # fewer than 2 bars
    result = build_risk_signals(history, "1w")
    first = result["signals"][0]
    assert first["id"] == "small_caps_lead"
    assert first["status"] == "unavailable"
    assert first["values"] is None


def test_risk_signals_uses_requested_range_same_as_flow_rows():
    # 1d uses the previous close as base, so craft last-2-bar moves explicitly.
    bars_iwm = bars_with_pct(pct=0, days=30)
    bars_spy = bars_with_pct(pct=0, days=30)
    bars_iwm[-2]["c"], bars_iwm[-1]["c"] = 100.0, 102.0
    bars_spy[-2]["c"], bars_spy[-1]["c"] = 100.0, 101.0
    result = build_risk_signals({"IWM": bars_iwm, "SPY": bars_spy}, "1d")
    first = result["signals"][0]
    assert first["status"] == "positive"
    assert first["values"]["IWM"] == 2.0
    assert first["values"]["SPY"] == 1.0


def test_risk_signals_reported_in_flows_payload_shape():
    history = risk_history(
        {"IWM": 2.0, "RSP": 2.0, "HYG": 2.0, "LQD": 1.0, "EEM": 2.0, "UUP": -1.0, "GLD": 0.5, "SPY": 1.0}
    )
    result = build_risk_signals(history, "1mo")
    assert set(result.keys()) == {"score", "of", "signals"}
    assert len(result["signals"]) == 6
    for signal in result["signals"]:
        assert set(signal.keys()) == {"id", "label", "description", "formula", "status", "values"}
