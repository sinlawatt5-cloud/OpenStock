import pytest

from app.providers import llm


HEADLINES = [
    {
        "title": "NVIDIA beats revenue expectations on AI chip demand",
        "source": "Reuters",
        "publishedAt": "2026-10-20T10:00:00+00:00",
        "tickers": ["NVDA"],
    },
    {
        "title": "NVIDIA announces new data center platform",
        "source": "CNBC",
        "publishedAt": "2026-10-20T12:00:00+00:00",
        "tickers": ["NVDA"],
    },
    {
        "title": "Apple supplier signals stronger phone orders",
        "source": "Bloomberg",
        "publishedAt": "2026-10-20T13:00:00+00:00",
        "tickers": ["AAPL"],
    },
]


def test_headline_hash_is_order_independent():
    a = llm.headline_hash(HEADLINES)
    b = llm.headline_hash(list(reversed(HEADLINES)))
    assert a == b and len(a) == 64


def test_rule_based_summary_has_three_bullets():
    text = llm.rule_based_summary(HEADLINES)
    lines = text.splitlines()
    assert 1 <= len(lines) <= 3
    assert all(line.startswith("•") for line in lines)
    assert "NVDA" in text


def test_rule_based_summary_handles_empty():
    assert "ยังไม่มี" in llm.rule_based_summary([])


class FakeSettings:
    gemini_api_key = ""
    openrouter_api_key = ""
    gemini_model = "gemini-3.5-flash-lite"
    openrouter_model = "minimax/minimax-m3.1-flash:free"
    llm_daily_cap = 100


@pytest.mark.asyncio
async def test_summary_falls_back_to_rules_and_caches(monkeypatch, db):
    monkeypatch.setattr(llm, "get_settings", lambda: FakeSettings())
    first = await llm.summarize(HEADLINES, db)
    assert first["provider"] == "rules"
    assert first["status" if "status" in first else "text"]
    second = await llm.summarize(HEADLINES, db)
    assert second["cached"] is True
    assert second["provider"] == "rules"
