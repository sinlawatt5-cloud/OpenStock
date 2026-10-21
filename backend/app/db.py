"""SQLite storage: TTL cache, seeded symbols, provider budgets, LLM cache."""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import get_settings
from .data.seed_symbols import SEED_SYMBOLS

_SCHEMA = """
CREATE TABLE IF NOT EXISTS cache (
    key TEXT PRIMARY KEY,
    payload TEXT NOT NULL,
    stored_at REAL NOT NULL,
    ttl REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS symbols (
    symbol TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    name_th TEXT NOT NULL,
    exchange TEXT,
    sector TEXT,
    industry TEXT,
    is_etf INTEGER DEFAULT 0,
    popularity_rank INTEGER,
    updated_at TEXT
);
CREATE TABLE IF NOT EXISTS provider_budget (
    provider TEXT NOT NULL,
    day TEXT NOT NULL,
    calls INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (provider, day)
);
CREATE TABLE IF NOT EXISTS llm_cache (
    headline_hash TEXT PRIMARY KEY,
    text TEXT NOT NULL,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    created_at REAL NOT NULL
);
"""


@dataclass
class CacheEntry:
    value: Any
    stored_at: float
    ttl: float


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Database:
    def __init__(self, path: str | None = None) -> None:
        self.path = Path(path or get_settings().openstock_db_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self.init_schema()
        self.seed_symbols()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def init_schema(self) -> None:
        with self._lock, self._connect() as conn:
            conn.executescript(_SCHEMA)

    # ------------------------------------------------------------------ cache
    def cache_get(self, key: str) -> CacheEntry | None:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT payload, stored_at, ttl FROM cache WHERE key = ?", (key,)
            ).fetchone()
        if not row:
            return None
        try:
            return CacheEntry(json.loads(row["payload"]), row["stored_at"], row["ttl"])
        except json.JSONDecodeError:
            return None

    def cache_set(self, key: str, value: Any, ttl: float) -> None:
        payload = json.dumps(value, ensure_ascii=False, default=str)
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT INTO cache(key, payload, stored_at, ttl) VALUES(?,?,?,?) "
                "ON CONFLICT(key) DO UPDATE SET payload=excluded.payload, "
                "stored_at=excluded.stored_at, ttl=excluded.ttl",
                (key, payload, time.time(), ttl),
            )

    def cache_age(self, key: str) -> float | None:
        entry = self.cache_get(key)
        return None if entry is None else time.time() - entry.stored_at

    # ---------------------------------------------------------------- symbols
    def seed_symbols(self) -> int:
        now = utc_now_iso()
        with self._lock, self._connect() as conn:
            conn.executemany(
                """
                INSERT INTO symbols(symbol, name, name_th, exchange, sector, industry,
                                    is_etf, popularity_rank, updated_at)
                VALUES(?,?,?,?,?,?,?,?,?)
                ON CONFLICT(symbol) DO UPDATE SET
                    name=excluded.name, name_th=excluded.name_th,
                    exchange=excluded.exchange, sector=excluded.sector,
                    industry=excluded.industry, is_etf=excluded.is_etf,
                    popularity_rank=excluded.popularity_rank,
                    updated_at=excluded.updated_at
                """,
                [
                    (
                        s["symbol"],
                        s["name"],
                        s["name_th"],
                        s.get("exchange", "NASDAQ"),
                        s.get("sector", ""),
                        s.get("industry", ""),
                        1 if s.get("is_etf") else 0,
                        i + 1,
                        now,
                    )
                    for i, s in enumerate(SEED_SYMBOLS)
                ],
            )
        return len(SEED_SYMBOLS)

    def list_symbols(self, limit: int = 30) -> list[dict[str, Any]]:
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM symbols ORDER BY popularity_rank ASC, symbol ASC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_symbol(self, symbol: str) -> dict[str, Any] | None:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM symbols WHERE symbol = ?", (symbol.upper(),)
            ).fetchone()
        return dict(row) if row else None

    def search_symbols(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        q = query.strip().upper()
        if not q:
            return []
        like = f"%{q}%"
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM symbols
                WHERE UPPER(symbol) LIKE ? OR UPPER(name) LIKE ? OR name_th LIKE ?
                ORDER BY (UPPER(symbol) = ?) DESC, popularity_rank ASC
                LIMIT ?
                """,
                (like, like, like, q, limit),
            ).fetchall()
        return [dict(r) for r in rows]

    def peers(self, sector: str, exclude: str, limit: int = 5) -> list[dict[str, Any]]:
        if not sector:
            return []
        with self._lock, self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM symbols WHERE sector = ? AND symbol != ? "
                "ORDER BY popularity_rank ASC LIMIT ?",
                (sector, exclude.upper(), limit),
            ).fetchall()
        return [dict(r) for r in rows]

    def symbol_count(self) -> int:
        with self._lock, self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS n FROM symbols").fetchone()
        return int(row["n"])

    # --------------------------------------------------------------- budgets
    def try_consume(self, provider: str, cap: int | None = None) -> bool:
        day = datetime.now(timezone.utc).date().isoformat()
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT calls FROM provider_budget WHERE provider = ? AND day = ?",
                (provider, day),
            ).fetchone()
            calls = int(row["calls"]) if row else 0
            if cap is not None and calls >= cap:
                return False
            conn.execute(
                "INSERT INTO provider_budget(provider, day, calls) VALUES(?,?,1) "
                "ON CONFLICT(provider, day) DO UPDATE SET calls = calls + 1",
                (provider, day),
            )
        return True

    def budget_used(self, provider: str) -> int:
        day = datetime.now(timezone.utc).date().isoformat()
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT calls FROM provider_budget WHERE provider = ? AND day = ?",
                (provider, day),
            ).fetchone()
        return int(row["calls"]) if row else 0

    # ------------------------------------------------------------ llm cache
    def llm_get(self, headline_hash: str) -> dict[str, Any] | None:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT text, provider, model, created_at FROM llm_cache WHERE headline_hash = ?",
                (headline_hash,),
            ).fetchone()
        return dict(row) if row else None

    def llm_set(
        self, headline_hash: str, text: str, provider: str, model: str
    ) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO llm_cache(headline_hash, text, provider, model, created_at) "
                "VALUES(?,?,?,?,?)",
                (headline_hash, text, provider, model, time.time()),
            )


_db: Database | None = None


def get_db() -> Database:
    global _db
    if _db is None:
        _db = Database()
    return _db
