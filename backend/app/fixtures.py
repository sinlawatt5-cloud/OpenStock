"""Offline fixture mode: seed the SQLite cache from recorded payloads."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from .db import Database

logger = logging.getLogger("openstock.fixtures")
FIXTURE_FILE = Path(__file__).parent / "fixtures" / "cache.json"
FIXTURE_TTL = 10 * 365 * 24 * 3600


def available() -> bool:
    return FIXTURE_FILE.exists()


def seed(db: Database) -> int:
    if not available():
        logger.warning("fixtures mode requested but %s is missing", FIXTURE_FILE)
        return 0
    try:
        payload = json.loads(FIXTURE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("could not read fixtures: %s", exc)
        return 0
    count = 0
    for key, value in payload.items():
        db.cache_set(key, value, FIXTURE_TTL)
        count += 1
    logger.info("seeded %s fixture cache keys", count)
    return count
