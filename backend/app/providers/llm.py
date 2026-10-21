"""News summarization: Gemini -> OpenRouter -> deterministic Thai fallback."""

from __future__ import annotations

import hashlib
import logging
import re
from typing import Any

import httpx

from ..config import get_settings
from ..db import Database, get_db

logger = logging.getLogger("openstock.llm")

GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPT = (
    "คุณเป็นนักวิเคราะห์ตลาดหุ้นที่เขียนภาษาไทยกระชับและเป็นกลาง "
    "สรุปจากพาดหัวข่าวที่ให้มาเท่านั้น ห้ามแต่งตัวเลข ราคา หรือข้อเท็จจริงใหม่ "
    "ห้ามให้คำแนะนำการลงทุน และห้ามใช้คำหวือหวา"
)

USER_TEMPLATE = """สรุปพาดหัวข่าวต่อไปนี้เป็นภาษาไทย 3 บรรทัด (ขึ้นต้นแต่ละบรรทัดด้วย \"• \")
แต่ละบรรทัดไม่เกิน 35 คำ ระบุชื่อบริษัทหรือ ticker ที่เกี่ยวข้องชัดเจน
ถ้าข่าวไม่เกี่ยวกับตลาดหุ้นให้ข้ามไป ใช้ภาษาธุรกิจที่เป็นกลาง

พาดหัวข่าว:
{headlines}
"""

_MODEL_CANDIDATES = [
    "gemini-3.5-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash-lite",
]

_resolved_gemini_model: str | None = None


def headline_hash(headlines: list[dict[str, Any]]) -> str:
    joined = "|".join(sorted(h.get("title", "") for h in headlines))
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def _format_headlines(headlines: list[dict[str, Any]], limit: int = 18) -> str:
    lines = []
    for item in headlines[:limit]:
        tickers = ",".join(item.get("tickers") or []) or "ตลาด"
        source = item.get("source") or ""
        published = (item.get("publishedAt") or "")[:10]
        lines.append(f"- [{tickers}] {item.get('title','')} ({source} {published})".strip())
    return "\n".join(lines)


def _clean(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```.*?\n|```$", "", text, flags=re.S)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"^\s*[-*]\s+", "• ", text, flags=re.M)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines[:5])


async def _gemini(prompt: str, api_key: str) -> tuple[str, str] | None:
    global _resolved_gemini_model
    settings = get_settings()
    candidates = (
        [_resolved_gemini_model] if _resolved_gemini_model else []
    ) + [settings.gemini_model, *_MODEL_CANDIDATES]
    seen: set[str] = set()
    body = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.35, "maxOutputTokens": 512},
    }
    async with httpx.AsyncClient(timeout=25) as client:
        for model in candidates:
            if not model or model in seen:
                continue
            seen.add(model)
            url = f"{GEMINI_BASE}/models/{model}:generateContent"
            try:
                response = await client.post(
                    url, headers={"x-goog-api-key": api_key}, json=body
                )
            except httpx.HTTPError as exc:
                logger.warning("gemini transport error: %s", exc)
                continue
            if response.status_code == 404:
                logger.info("gemini model %s not found, trying next", model)
                continue
            if response.status_code != 200:
                logger.warning("gemini %s returned %s", model, response.status_code)
                break
            try:
                data = response.json()
                parts = data["candidates"][0]["content"]["parts"]
                text = "".join(p.get("text", "") for p in parts)
            except (KeyError, IndexError, ValueError):
                continue
            if text.strip():
                _resolved_gemini_model = model
                return _clean(text), model
    return None


async def _openrouter(prompt: str, api_key: str) -> tuple[str, str] | None:
    settings = get_settings()
    payload = {
        "model": settings.openrouter_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.35,
        "max_tokens": 420,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-Title": "OpenStock",
    }
    try:
        async with httpx.AsyncClient(timeout=35) as client:
            response = await client.post(OPENROUTER_URL, headers=headers, json=payload)
    except httpx.HTTPError as exc:
        logger.warning("openrouter transport error: %s", exc)
        return None
    if response.status_code != 200:
        logger.warning("openrouter returned %s", response.status_code)
        return None
    try:
        data = response.json()
        text = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, ValueError):
        return None
    if not text or not text.strip():
        return None
    return _clean(text), settings.openrouter_model


def rule_based_summary(headlines: list[dict[str, Any]]) -> str:
    """Deterministic Thai summary used when no LLM is available."""
    if not headlines:
        return "ยังไม่มีพาดหัวข่าวเพียงพอสำหรับสรุปในขณะนี้"
    buckets: dict[str, list[dict[str, Any]]] = {}
    for item in headlines:
        tickers = item.get("tickers") or []
        key = tickers[0] if tickers else "ภาพรวมตลาด"
        buckets.setdefault(key, []).append(item)
    ranked = sorted(buckets.items(), key=lambda kv: len(kv[1]), reverse=True)[:3]
    lines = []
    for ticker, items in ranked:
        first = items[0].get("title", "").strip().rstrip(".")
        extra = f" และอีก {len(items) - 1} ข่าว" if len(items) > 1 else ""
        lines.append(f"• {ticker}: {first}{extra}")
    if len(lines) < 3:
        lines.append(
            f"• ภาพรวม: มีพาดหัวที่เกี่ยวข้อง {len(headlines)} ข่าว จาก "
            f"{len(buckets)} กลุ่มสินทรัพย์"
        )
    return "\n".join(lines[:3])


async def summarize(headlines: list[dict[str, Any]], db: Database | None = None) -> dict[str, Any]:
    """Return {text, provider, model, cached} using the best available route."""
    settings = get_settings()
    db = db or get_db()

    if not headlines:
        return {
            "text": rule_based_summary(headlines),
            "provider": "rules",
            "model": "rule-based",
            "cached": False,
        }

    digest = headline_hash(headlines)
    cached = db.llm_get(digest)
    if cached:
        return {
            "text": cached["text"],
            "provider": cached["provider"],
            "model": cached["model"],
            "cached": True,
        }

    prompt = USER_TEMPLATE.format(headlines=_format_headlines(headlines))
    budget_ok = db.try_consume("llm", cap=settings.llm_daily_cap)

    if budget_ok:
        if settings.gemini_api_key:
            result = await _gemini(prompt, settings.gemini_api_key)
            if result:
                text, model = result
                db.llm_set(digest, text, "gemini", model)
                return {"text": text, "provider": "gemini", "model": model, "cached": False}
        if settings.openrouter_api_key:
            result = await _openrouter(prompt, settings.openrouter_api_key)
            if result:
                text, model = result
                db.llm_set(digest, text, "openrouter", model)
                return {
                    "text": text,
                    "provider": "openrouter",
                    "model": model,
                    "cached": False,
                }

    text = rule_based_summary(headlines)
    db.llm_set(digest, text, "rules", "rule-based")
    return {"text": text, "provider": "rules", "model": "rule-based", "cached": False}


def configured() -> dict[str, bool]:
    settings = get_settings()
    return {
        "gemini": bool(settings.gemini_api_key),
        "openrouter": bool(settings.openrouter_api_key),
    }
