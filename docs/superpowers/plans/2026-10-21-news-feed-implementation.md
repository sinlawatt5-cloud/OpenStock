# 24-Hour Thai Stock News Feed Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an on-demand 24-hour US-stock Timeline Feed that aggregates verified free sources, deduplicates items, translates and summarizes them into Thai with Gemini/OpenRouter fallback, and remains usable during partial failures.

**Architecture:** Persist normalized articles, symbol links, translation status, and refresh-run state in SQLite. A user-triggered asynchronous refresh gathers Yahoo/RSS/SEC sources, processes only new content hashes through Gemini 3.5 Flash Lite then OpenRouter, and exposes cursor-paginated FastAPI endpoints consumed by a responsive React Summary + Timeline Feed page.

**Tech Stack:** Python 3.12, FastAPI, SQLite, httpx, defusedxml, pytest/respx, React 19, TypeScript, TanStack Query, React Router, Vitest/jsdom, Playwright.

**Spec:** `docs/superpowers/specs/2026-10-21-news-feed-and-logo-design.md`

**Dependency:** Complete `docs/superpowers/plans/2026-10-21-global-logo-system-implementation.md` first. This plan consumes `cached_logo_url(symbol)` and `/api/logos/{symbol}`.

## Global Constraints

- Track only Watchlist symbols supplied by the browser, cached Movers, and the existing Popular 30 symbols.
- The displayed window is exactly the latest 24 hours using trustworthy source publication timestamps; never substitute fetch time for missing publication time.
- Persist articles for 7 days for dedupe/audit and prune older rows after successful or partial refreshes.
- Primary AI model is exactly `gemini-3.5-flash-lite`; translation falls back to the configured OpenRouter model, then untranslated English.
- AI input is limited to stable ID, ticker/company names, title, sanitized provider snippet, source, and publication time; never scrape full articles or bypass paywalls.
- Every displayed item retains source, original URL, original title, and publication time.
- Refresh is manual only; no scheduler or recurring background polling.
- Feed remains readable from SQLite during refresh and partial provider failures.
- RSS/Atom endpoints are allowlisted. Enforce HTTPS, bounded response size, timeouts, redirect checks, safe XML parsing, and HTML sanitization.
- Do not expose API keys, prompts, or internal provider errors to frontend responses.
- Preserve `/api/news` and `/api/news/summary` contracts used by the Dashboard.
- Preserve the approved light theme and Timeline Feed layout; mobile 390px must have no horizontal overflow.
- Current workspace contains uncommitted risk-on changes. Before execution, preserve them in a commit/stash and use a branch/worktree that includes them.
- If pnpm `minimumReleaseAge` policy blocks installation, use `pnpm install --config.minimumReleaseAge=0` only for the install command; do not persistently weaken machine policy.

---

## File Structure

### Backend

- Modify `backend/pyproject.toml`, `backend/uv.lock` — add `defusedxml`.
- Modify `backend/app/config.py` — source limits, SEC User-Agent, translation batch/max settings.
- Modify `backend/app/db.py` — article/symbol/run schema and repository methods.
- Create `backend/app/providers/rss.py` — bounded allowlisted RSS/Atom fetch and parse.
- Modify `backend/app/providers/yahoo.py` — expose normalized Yahoo ticker news with snippet and stable source URL.
- Modify `backend/app/providers/llm.py` — strict structured batch translation and provider fallback.
- Create `backend/app/services/news_normalize.py` — URL canonicalization, timestamp parsing, HTML cleanup, ticker detection, dedupe.
- Create `backend/app/services/news_refresh.py` — symbol-universe assembly, ingestion, translation, pruning, in-process task lifecycle.
- Modify `backend/app/services/news.py` — 24-hour query/summary service while preserving legacy methods.
- Modify `backend/app/routers/news.py` — 24h feed, refresh, status, summary endpoints.
- Create `backend/tests/fixtures/news/` — deterministic RSS/Atom fixtures.
- Create `backend/tests/test_news_sources.py`, `test_news_storage.py`, `test_news_refresh.py`.
- Modify `backend/tests/test_news.py`, `test_api.py`.

### Frontend

- Modify `frontend/src/lib/types.ts` — feed/run/summary contracts.
- Modify `frontend/src/lib/api.ts` — add typed POST helper.
- Create `frontend/src/features/news/NewsFilters.tsx`.
- Create `frontend/src/features/news/NewsTimeline.tsx`.
- Create `frontend/src/features/news/NewsDigest.tsx`.
- Create `frontend/src/features/news/RefreshProgress.tsx`.
- Create `frontend/src/pages/NewsPage.tsx`.
- Modify `frontend/src/App.tsx`, `components/TopNav.tsx`, `components/AppShell.tsx`, `features/overview/NewsPanel.tsx`, `styles/index.css`.
- Create component tests under `frontend/src/features/news/*.test.tsx` and `frontend/src/pages/NewsPage.test.tsx`.
- Modify `frontend/e2e/smoke.spec.ts`.

---

### Task 1: Add News Persistence and Repository Methods

**Files:**
- Modify: `backend/app/db.py`
- Create: `backend/tests/test_news_storage.py`

**Interfaces:**
- Produces: `Database.news_upsert(article: dict[str, Any]) -> tuple[str, bool]` where bool means inserted.
- Produces: `Database.news_link_symbols(article_id: str, symbols: list[dict[str, Any]]) -> None`.
- Produces: `Database.news_get_by_hash(content_hash: str) -> dict[str, Any] | None`.
- Produces: `Database.news_mark_translation(article_id: str, *, status: str, title_th: str | None, summary_th: str | None, provider: str, model: str) -> None`.
- Produces: `Database.news_list_24h(filters: dict[str, Any], limit: int, cursor: tuple[str, str] | None, now_ts: float) -> tuple[list[dict[str, Any]], tuple[str, str] | None]`.
- Produces: `Database.refresh_create(run_id: str)`, `refresh_update`, `refresh_get`, `refresh_active`.
- Produces: `Database.news_prune(before_ts: float) -> int`.

- [ ] **Step 1: Write failing schema/repository tests**

```python
from datetime import datetime, timezone

ARTICLE = {
    "id": "article-1",
    "title_original": "NVIDIA launches a new platform",
    "description_original": "The company announced a data-center platform.",
    "canonical_url": "https://example.com/nvidia-platform",
    "source": "Example Wire",
    "published_at": "2026-10-21T12:00:00+00:00",
    "translation_status": "pending",
    "translation_provider": "none",
    "translation_model": "",
    "content_hash": "hash-1",
}


def test_article_upsert_and_symbol_links(db):
    article_id, inserted = db.news_upsert(ARTICLE)
    assert (article_id, inserted) == ("article-1", True)
    db.news_link_symbols(article_id, [
        {"symbol": "NVDA", "confidence": 1.0, "detection_source": "provider"}
    ])
    rows, cursor = db.news_list_24h({}, 30, None,
        datetime(2026, 10, 21, 16, tzinfo=timezone.utc).timestamp())
    assert cursor is None
    assert rows[0]["symbols"][0]["symbol"] == "NVDA"


def test_second_upsert_is_not_inserted(db):
    db.news_upsert(ARTICLE)
    _, inserted = db.news_upsert(ARTICLE)
    assert inserted is False


def test_cursor_is_stable_for_equal_timestamps(db):
    seed_articles_with_equal_times(db, count=3)
    first, cursor = db.news_list_24h({}, 2, None, NOW_TS)
    second, _ = db.news_list_24h({}, 2, cursor, NOW_TS)
    assert [row["id"] for row in first + second] == ["c", "b", "a"]
```

Also test translation updates, filters by symbols/source/status, active-run reuse, and pruning cascade behavior.

- [ ] **Step 2: Run storage tests and verify failure**

Run: `cd backend && uv run --locked --group dev pytest tests/test_news_storage.py -v`  
Expected: FAIL because repository methods do not exist.

- [ ] **Step 3: Add exact schema**

Add `news_articles`, `news_article_symbols`, and `news_refresh_runs` exactly as specified in the design. Use `published_at REAL` for indexed UTC timestamps and return ISO strings at the service boundary. Add foreign keys with `ON DELETE CASCADE`, enable `PRAGMA foreign_keys=ON` in `_connect`, and add indexes for publication time, translation status, hash, source, and symbol joins.

- [ ] **Step 4: Implement repository methods with deterministic cursor ordering**

Order by `published_at DESC, id DESC`; encode/decode cursor outside the DB as the tuple `(published_at_iso, id)`. Parameterize all SQL and whitelist sort/filter clauses.

- [ ] **Step 5: Run storage tests**

Run: `cd backend && uv run --locked --group dev pytest tests/test_news_storage.py -v`  
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/db.py backend/tests/test_news_storage.py
git commit -m "feat: add persistent news feed storage"
```

---

### Task 2: Implement Safe RSS and Atom Providers

**Files:**
- Modify: `backend/pyproject.toml`
- Modify: `backend/uv.lock`
- Modify: `backend/app/config.py`
- Create: `backend/app/providers/rss.py`
- Create: `backend/tests/fixtures/news/yahoo-aapl.xml`
- Create: `backend/tests/fixtures/news/cnbc.xml`
- Create: `backend/tests/fixtures/news/marketwatch.xml`
- Create: `backend/tests/fixtures/news/google-aapl.xml`
- Create: `backend/tests/fixtures/news/sec-aapl.xml`
- Create: `backend/tests/test_news_sources.py`

**Interfaces:**
- Produces: `FeedSource(key: str, url: str, kind: Literal["rss", "atom"], default_source: str, symbol: str | None)`.
- Produces: `async fetch_feed(source: FeedSource) -> list[dict[str, Any]]`.
- Produces normalized provider records with keys `title`, `description`, `url`, `source`, `publishedAt`, `tickers`, `providerKey`.

- [ ] **Step 1: Add parser tests against committed fixtures**

```python
@pytest.mark.parametrize(
    ("fixture", "expected_source"),
    [
        ("yahoo-aapl.xml", "Yahoo Finance"),
        ("cnbc.xml", "CNBC"),
        ("marketwatch.xml", "MarketWatch"),
        ("google-aapl.xml", "Reuters"),
        ("sec-aapl.xml", "SEC"),
    ],
)
def test_parse_feed_fixture(fixture, expected_source):
    items = rss.parse_feed_bytes(load_fixture(fixture), default_source=expected_source)
    assert items
    assert items[0]["title"]
    assert items[0]["url"].startswith("https://")
    assert items[0]["publishedAt"]
```

Add tests rejecting DOCTYPE/entity payloads, responses larger than the configured limit, non-HTTPS redirects, and sources outside the allowlist.

- [ ] **Step 2: Run tests and verify missing module failure**

Run: `cd backend && uv run --locked --group dev pytest tests/test_news_sources.py -v`  
Expected: FAIL because `providers.rss` does not exist.

- [ ] **Step 3: Add `defusedxml` dependency**

Run: `cd backend && uv add defusedxml`  
Expected: `pyproject.toml` and `uv.lock` update with a compatible `defusedxml` release.

- [ ] **Step 4: Add exact configuration defaults**

```python
openstock_news_http_timeout: float = 15.0
openstock_news_max_feed_bytes: int = 2_000_000
openstock_news_max_redirects: int = 3
openstock_news_google_fallback_min_items: int = 5
openstock_sec_user_agent: str = "OpenStock contact@example.com"
openstock_news_translation_batch_size: int = 6
openstock_news_max_translations_per_refresh: int = 48
```

Document that production must replace the SEC contact placeholder through `.env` before deployment.

- [ ] **Step 5: Implement allowlisted source builders**

Expose builders for Yahoo per ticker, CNBC, MarketWatch, Google fallback per ticker, and SEC by CIK. URLs must be constructed from validated ticker/CIK values, never accepted directly from request input.

- [ ] **Step 6: Parse RSS/Atom with `defusedxml.ElementTree`**

Support RSS `<item>` and Atom `<entry>`, namespaces, RFC 822/ISO timestamps, `description`/`summary`, canonical links, Yahoo related tickers, Google publisher extraction, and SEC source labeling. Strip markup to plain text before returning.

- [ ] **Step 7: Implement bounded HTTP fetching**

Use manual redirect handling so every target is checked for HTTPS and allowlisted hostname. Stream into memory up to the byte limit. Send provider-appropriate User-Agent, including configured SEC identity for `sec.gov`.

- [ ] **Step 8: Run source tests**

Run: `cd backend && uv run --locked --group dev pytest tests/test_news_sources.py -v`  
Expected: PASS without live network access.

- [ ] **Step 9: Commit**

```bash
git add backend/pyproject.toml backend/uv.lock backend/app/config.py backend/app/providers/rss.py backend/tests/fixtures/news backend/tests/test_news_sources.py
git commit -m "feat: add safe free news feed providers"
```

---

### Task 3: Normalize, Filter, Detect Symbols, and Dedupe

**Files:**
- Create: `backend/app/services/news_normalize.py`
- Create: `backend/tests/test_news_normalize.py`

**Interfaces:**
- Consumes: provider records from Task 2 and symbol records from `Database.list_symbols`.
- Produces: `normalize_article(raw: dict[str, Any], *, now: datetime, queried_symbol: str | None = None) -> dict[str, Any] | None`.
- Produces: `dedupe_articles(items: list[dict[str, Any]]) -> list[dict[str, Any]]`.
- Produces: `canonicalize_url(url: str) -> str | None`.

- [ ] **Step 1: Write failing normalization tests**

```python
def test_canonical_url_removes_tracking_but_keeps_identity_params():
    url = "https://example.com/story?id=42&utm_source=rss&guccounter=1"
    assert canonicalize_url(url) == "https://example.com/story?id=42"


def test_rejects_article_older_than_24_hours():
    raw = make_raw(publishedAt="2026-10-20T14:59:59+00:00")
    assert normalize_article(raw, now=datetime(2026, 10, 21, 15, tzinfo=timezone.utc)) is None


def test_provider_ticker_has_highest_confidence():
    raw = make_raw(tickers=["NVDA"], title="NVIDIA launches platform")
    article = normalize_article(raw, now=NOW)
    assert article["symbols"] == [
        {"symbol": "NVDA", "confidence": 1.0, "detection_source": "provider"}
    ]


def test_dedupe_prefers_richer_direct_publisher_item():
    direct = make_normalized(source="Reuters", description_original="Detailed description")
    aggregate = make_normalized(source="Google News", description_original="")
    assert dedupe_articles([aggregate, direct]) == [direct]
```

- [ ] **Step 2: Run tests and verify failure**

Run: `cd backend && uv run --locked --group dev pytest tests/test_news_normalize.py -v`  
Expected: FAIL because module/functions do not exist.

- [ ] **Step 3: Implement canonical URL handling**

Allow HTTPS only; lowercase hostname; remove fragments and tracking keys `utm_*`, `guccounter`, `oc`, `gclid`, `fbclid`; preserve other query parameters in sorted order.

- [ ] **Step 4: Implement timestamp and 24-hour boundary rules**

Accept timezone-aware ISO/RFC 822 values, convert to UTC, and include articles where `now - 24h <= published_at <= now + 5m`. Reject missing/invalid timestamps.

- [ ] **Step 5: Implement symbol detection priority**

Priority: provider tickers (1.0), queried symbol (0.9), exact catalog ticker/company-name match in title/snippet (0.7). Limit to valid catalog symbols and three primary display symbols while retaining all links in storage.

- [ ] **Step 6: Implement stable IDs and two-stage dedupe**

Use SHA-256 over canonical URL when present, otherwise normalized source/title/time. Dedupe canonical URL first and normalized title hash second; rank richer description, trustworthy publisher, and explicit time above aggregator copies.

- [ ] **Step 7: Run normalization tests**

Run: `cd backend && uv run --locked --group dev pytest tests/test_news_normalize.py -v`  
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add backend/app/services/news_normalize.py backend/tests/test_news_normalize.py
git commit -m "feat: normalize and deduplicate stock news"
```

---

### Task 4: Add Strict Gemini Translation With OpenRouter Fallback

**Files:**
- Modify: `backend/app/providers/llm.py`
- Modify: `backend/tests/test_news.py`

**Interfaces:**
- Produces: `async translate_news_batch(items: list[dict[str, Any]], db: Database | None = None) -> list[dict[str, Any]]`.
- Each result has `id`, `titleTh`, `summaryTh`, `status`, `provider`, `model`.
- Status mapping: Gemini=`ready`, OpenRouter=`fallback`, both fail=`failed` with null Thai fields.

- [ ] **Step 1: Write failing structured translation tests**

Use `respx` for exact Gemini/OpenRouter requests:

```python
@pytest.mark.asyncio
async def test_translation_prefers_exact_gemini_model(monkeypatch, db, respx_mock):
    monkeypatch.setattr(llm, "get_settings", lambda: TranslationSettings())
    route = respx_mock.post(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent"
    ).respond(200, json=gemini_json('[{"id":"a1","titleTh":"ข่าวไทย","summaryTh":"สรุปครบถ้วน"}]'))
    result = await llm.translate_news_batch([translation_item("a1")], db)
    assert route.called
    assert result[0]["status"] == "ready"
    assert result[0]["provider"] == "gemini"


@pytest.mark.asyncio
async def test_translation_falls_back_to_openrouter(monkeypatch, db, respx_mock):
    mock_gemini_failure(respx_mock, status=429)
    mock_openrouter_success(respx_mock, id="a1")
    result = await llm.translate_news_batch([translation_item("a1")], db)
    assert result[0]["status"] == "fallback"
    assert result[0]["provider"] == "openrouter"
```

Also test malformed JSON, missing IDs, title/summary length limits, invented IDs, numeric fidelity validation, cache reuse, and both-provider failure.

- [ ] **Step 2: Run targeted tests and verify failure**

Run: `cd backend && uv run --locked --group dev pytest tests/test_news.py -k translation -v`  
Expected: FAIL because `translate_news_batch` does not exist.

- [ ] **Step 3: Define strict system/user prompts**

Prompt must require a JSON array, exact input IDs, Thai business language, 1–2 sentence summaries up to 60 Thai words, no investment advice, and no facts/numbers absent from input. Include each item's company names/tickers, title, sanitized snippet, source, and published time.

- [ ] **Step 4: Call only the configured exact Gemini model**

Create a translation-specific Gemini helper that does not iterate `_MODEL_CANDIDATES`. Use temperature `0.15`, JSON response MIME/schema when supported, and bounded output tokens based on batch size.

- [ ] **Step 5: Validate structured output before caching**

Require one result per known ID, non-empty `titleTh`/`summaryTh`, maximum lengths, and preservation of digit sequences from source text when those digits appear in the generated output context. Invalid Gemini output triggers OpenRouter for that batch; invalid OpenRouter output returns `failed`.

- [ ] **Step 6: Cache each article separately by `content_hash`**

Use a distinct cache key namespace such as `news-item:{content_hash}` so the legacy aggregate summary cache remains compatible. Do not consume LLM budget for cached items.

- [ ] **Step 7: Run translation and legacy news tests**

Run: `cd backend && uv run --locked --group dev pytest tests/test_news.py -v`  
Expected: PASS, including existing aggregate summary tests.

- [ ] **Step 8: Commit**

```bash
git add backend/app/providers/llm.py backend/tests/test_news.py
git commit -m "feat: translate news with Gemini and OpenRouter fallback"
```

---

### Task 5: Implement Refresh Orchestration

**Files:**
- Create: `backend/app/services/news_refresh.py`
- Create: `backend/tests/test_news_refresh.py`
- Modify: `backend/app/services/logos.py`

**Interfaces:**
- Consumes: feed providers, normalization, DB repository, translation, `resolve_logo`.
- Produces: `async start_refresh(watchlist_symbols: list[str]) -> dict[str, Any]`.
- Produces: `get_refresh(run_id: str) -> dict[str, Any] | None`.
- Produces internal `async _run_refresh(run_id: str, symbols: list[str]) -> None` tracked in a strong-reference task set.

- [ ] **Step 1: Write failing orchestration tests**

```python
@pytest.mark.asyncio
async def test_refresh_reuses_active_run(monkeypatch, db):
    wire_refresh_dependencies(monkeypatch, db)
    first = await news_refresh.start_refresh(["NVDA"])
    second = await news_refresh.start_refresh(["AAPL"])
    assert second["id"] == first["id"]


@pytest.mark.asyncio
async def test_partial_provider_failure_preserves_successes(monkeypatch, db):
    wire_refresh_dependencies(monkeypatch, db, fail_sources={"cnbc"})
    run = await news_refresh.start_refresh(["NVDA"])
    await news_refresh.wait_for_test_run(run["id"])
    stored, _ = db.news_list_24h({}, 30, None, NOW_TS)
    assert stored
    assert db.refresh_get(run["id"])["status"] == "partial"
```

Also test symbol union/dedupe, Popular 30 inclusion, Movers cache inclusion, Google fallback threshold, translation cap, logo resolution, no-new-article completion, full failure preserving old rows, and 7-day pruning.

- [ ] **Step 2: Run tests and verify missing service failure**

Run: `cd backend && uv run --locked --group dev pytest tests/test_news_refresh.py -v`  
Expected: FAIL because service does not exist.

- [ ] **Step 3: Implement validated symbol-universe assembly**

Validate Watchlist symbols with `^[A-Z0-9.-]{1,12}$`, cap browser input at the existing `WATCHLIST_MAX`, add symbols from the three mover cache keys, add `Database.list_symbols(30)`, preserve order, and dedupe.

- [ ] **Step 4: Implement staged refresh lifecycle**

Create a UUID run, update exact stages `fetching`, `normalizing`, `translating`, `resolving_logos`, `completed`; store provider-level sanitized errors. Use `asyncio.create_task`, retain tasks in `_tasks`, and remove them in a done callback.

- [ ] **Step 5: Fetch sources with bounded concurrency**

Use `asyncio.Semaphore(6)`. Fetch Yahoo/yfinance per symbol plus market feeds once. Use Google per ticker only when primary normalized items for that ticker are below the configured minimum. SEC requires known CIK mappings; symbols without CIK skip SEC without error.

- [ ] **Step 6: Persist before translating**

Normalize/dedupe, upsert source records, link symbols, then select inserted/pending/failed records up to the translation cap. This guarantees English fallback is visible even when AI fails.

- [ ] **Step 7: Translate in configured batches and update counters**

Process batches sequentially to protect free-tier quotas. Save each result immediately and update run counters after each batch.

- [ ] **Step 8: Resolve logos without blocking article persistence**

Resolve unique symbols with bounded concurrency. Logo errors are recorded as warnings and never fail the news refresh.

- [ ] **Step 9: Prune 7-day data only after successful/partial processing**

Call `news_prune(now - 7 days)` for `completed`/`partial`, never after full failure.

- [ ] **Step 10: Run orchestration tests**

Run: `cd backend && uv run --locked --group dev pytest tests/test_news_refresh.py -v`  
Expected: PASS.

- [ ] **Step 11: Commit**

```bash
git add backend/app/services/news_refresh.py backend/app/services/logos.py backend/tests/test_news_refresh.py
git commit -m "feat: orchestrate on-demand news refreshes"
```

---

### Task 6: Add 24-Hour Feed, Summary, Refresh, and Status APIs

**Files:**
- Modify: `backend/app/services/news.py`
- Modify: `backend/app/routers/news.py`
- Modify: `backend/tests/test_api.py`
- Create: `backend/tests/test_news_api.py`

**Interfaces:**
- Produces: `GET /api/news/24h`.
- Produces: `GET /api/news/24h/summary`.
- Produces: `POST /api/news/refresh` with JSON `{watchlistSymbols: string[]}`.
- Produces: `GET /api/news/refresh/{run_id}`.
- Preserves: existing `/api/news` and `/api/news/summary`.

- [ ] **Step 1: Write failing API contract tests**

```python
def test_feed_returns_cursor_and_logo_metadata(monkeypatch, db):
    seed_ready_news(db)
    response = client.get("/api/news/24h?scope=all&limit=1")
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"items", "summary", "nextCursor", "asOf", "lastRefresh", "warnings"}
    assert body["items"][0]["symbols"][0]["logoUrl"] == "/api/logos/NVDA"


def test_refresh_rejects_invalid_watchlist_symbol():
    response = client.post("/api/news/refresh", json={"watchlistSymbols": ["../../etc"]})
    assert response.status_code == 422


def test_legacy_news_contract_remains_available():
    assert client.get("/api/news").status_code in {200, 503}
    assert "/api/news/summary" in client.get("/api/openapi.json").json()["paths"]
```

Also test cursor round-trip, each filter, malformed cursor=422, run 404, active run=202, summary cache, and no API keys/internal tracebacks in errors.

- [ ] **Step 2: Run tests and verify missing-route failures**

Run: `cd backend && uv run --locked --group dev pytest tests/test_news_api.py tests/test_api.py -v`  
Expected: FAIL with missing endpoints.

- [ ] **Step 3: Add Pydantic request model and query validation**

Define `RefreshRequest` with at most `WATCHLIST_MAX` symbols and field validation to uppercase/dedupe tickers. Use `Literal` for scope/translation and bounded `limit` 1–50.

- [ ] **Step 4: Implement opaque cursor encoding**

Encode JSON `[published_at_iso, id]` with URL-safe base64; reject invalid shape/UTF-8/time with HTTP 422. Do not expose SQL offsets.

- [ ] **Step 5: Implement feed response mapping**

Map database snake_case to frontend camelCase; include original/Thai fields, symbols with `logoUrl`, source, original URL, provider badge, and refresh metadata. `summary` may be null while summary generation is pending.

- [ ] **Step 6: Implement cached 24-hour digest**

Reuse aggregate LLM infrastructure but hash ordered ready article IDs/content hashes. Return Thai bullet summary, provider/model, source count, cached flag, and as-of time. Do not include untranslated items in the digest input.

- [ ] **Step 7: Register endpoints before `/{run_id}` ambiguity can occur**

Use explicit paths `/24h`, `/24h/summary`, `/refresh`, `/refresh/{run_id}` in `routers/news.py`. Preserve current root and `/summary` handlers unchanged.

- [ ] **Step 8: Run API and full backend tests**

Run: `cd backend && uv run --locked --group dev pytest`  
Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add backend/app/services/news.py backend/app/routers/news.py backend/tests/test_news_api.py backend/tests/test_api.py
git commit -m "feat: expose 24-hour news feed APIs"
```

---

### Task 7: Add Frontend API Contracts and Navigation

**Files:**
- Modify: `frontend/src/lib/types.ts`
- Modify: `frontend/src/lib/api.ts`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/TopNav.tsx`
- Modify: `frontend/src/components/AppShell.tsx`
- Modify: `frontend/src/features/overview/NewsPanel.tsx`
- Create: `frontend/src/pages/NewsPage.tsx`
- Create: `frontend/src/pages/NewsPage.test.tsx`

**Interfaces:**
- Produces: `apiPost<TBody, TResponse>(path: string, body: TBody): Promise<TResponse>`.
- Produces: `NewsFeedResponse`, `NewsFeedItem`, `NewsRefreshRun`, `NewsDigestResponse` types.
- Produces: route `/news` and navigation label `ข่าว 24 ชม.`.

- [ ] **Step 1: Write failing route/render test**

```tsx
// @vitest-environment jsdom
it('registers the news page route and heading', async () => {
  renderAppAt('/news', { newsFeed: emptyFeedFixture() })
  expect(await screen.findByRole('heading', { name: 'ข่าวหุ้น 24 ชั่วโมง' })).toBeTruthy()
})
```

Use a test QueryClient with retries disabled and mock `fetch` responses; clean up after each test.

- [ ] **Step 2: Run test and verify route failure**

Run: `cd frontend && ./node_modules/.bin/vitest run src/pages/NewsPage.test.tsx`  
Expected: FAIL because `/news` and `NewsPage` do not exist.

- [ ] **Step 3: Add exact TypeScript contracts**

Define unions:

```ts
export type NewsTranslationStatus = 'pending' | 'ready' | 'fallback' | 'failed'
export type NewsRefreshStatus = 'queued' | 'fetching' | 'normalizing' | 'translating' | 'resolving_logos' | 'completed' | 'partial' | 'failed'
```

Define all camelCase fields matching Task 6; avoid `any`.

- [ ] **Step 4: Add JSON POST helper**

Mirror `apiGet` error handling, set `Content-Type: application/json`, serialize body, and retain typed error details without exposing raw HTML responses.

- [ ] **Step 5: Add route, nav item, dashboard link, and source credit**

Import `NewsPage` in `App.tsx`; add `<Route path="news" element={<NewsPage />} />`; add a `NavLink` labeled `ข่าว 24 ชม.` in `TopNav.tsx` with responsive behavior consistent with current tabs. Add a `ดูข่าวทั้งหมด` link from the existing Dashboard `NewsPanel` to `/news`. Update the AppShell footer source line to mention Yahoo Finance, CNBC, MarketWatch, SEC, Finnhub, and Alpha Vantage without claiming that every source supplies every screen.

- [ ] **Step 6: Create a minimal query-backed page shell**

Use `useSearchParams`, query `/news/24h`, show the approved heading, count/last refresh metadata, loading/error/empty shells, and no final visual styling yet.

- [ ] **Step 7: Run component tests and typecheck**

Run:

```bash
cd frontend
./node_modules/.bin/vitest run src/pages/NewsPage.test.tsx
./node_modules/.bin/tsc -b
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add frontend/src/lib/types.ts frontend/src/lib/api.ts frontend/src/App.tsx frontend/src/components/TopNav.tsx frontend/src/components/AppShell.tsx frontend/src/features/overview/NewsPanel.tsx frontend/src/pages/NewsPage.tsx frontend/src/pages/NewsPage.test.tsx
git commit -m "feat: add news route and frontend contracts"
```

---

### Task 8: Build Summary, Filters, Timeline, and Refresh Components

**Files:**
- Create: `frontend/src/features/news/NewsDigest.tsx`
- Create: `frontend/src/features/news/NewsFilters.tsx`
- Create: `frontend/src/features/news/NewsTimeline.tsx`
- Create: `frontend/src/features/news/RefreshProgress.tsx`
- Create: `frontend/src/features/news/NewsTimeline.test.tsx`
- Create: `frontend/src/features/news/NewsFilters.test.tsx`
- Create: `frontend/src/features/news/RefreshProgress.test.tsx`
- Modify: `frontend/src/pages/NewsPage.tsx`
- Modify: `frontend/src/pages/NewsPage.test.tsx`
- Modify: `frontend/src/styles/index.css`

**Interfaces:**
- Consumes: Task 7 types/helpers and shared `Avatar`, `SkeletonBlock`, `ErrorState`.
- Produces approved Summary + Timeline Feed desktop/mobile experience.

- [ ] **Step 1: Write failing Timeline tests**

```tsx
it('renders newest items first with source, ticker, model and original link', () => {
  render(<NewsTimeline items={twoNewsItemsOutOfOrder()} />)
  const articles = screen.getAllByRole('article')
  expect(articles[0].textContent).toContain('NVDA')
  expect(articles[0].textContent).toContain('Gemini')
  expect(screen.getAllByRole('link', { name: 'อ่านต้นฉบับ' })[0].getAttribute('target')).toBe('_blank')
})

it('shows English fallback when Thai translation failed', () => {
  render(<NewsTimeline items={[failedTranslationItem()]} />)
  expect(screen.getByText('รอแปล')).toBeTruthy()
  expect(screen.getByText(failedTranslationItem().titleOriginal)).toBeTruthy()
})
```

Also test maximum three ticker chips plus `+N`, logo fallback, and time/source metadata.

- [ ] **Step 2: Write failing filter URL tests**

Render `NewsFilters` with current URL params; click Watchlist/source/status chips; assert `setSearchParams` receives merged parameters and unrelated params are preserved.

- [ ] **Step 3: Write failing refresh-state tests**

Cover disabled duplicate click, stage labels, partial warning, failed state, and terminal polling stop callback.

- [ ] **Step 4: Run component tests and verify failures**

Run: `cd frontend && ./node_modules/.bin/vitest run src/features/news`  
Expected: FAIL because components do not exist.

- [ ] **Step 5: Implement `NewsTimeline`**

Sort defensively by `publishedAt` descending; use semantic `<article>` elements; render shared Avatar on the timeline rail; choose `titleTh ?? titleOriginal` and `summaryTh ?? descriptionOriginal`; show source, `timeAgo`, up to three ticker chips, provider badge, and secure original link.

- [ ] **Step 6: Implement `NewsDigest` and `NewsFilters`**

Digest displays cached summary, provider/model badge, source/item counts, and its own loading/fallback states. Filters are URL-backed chips/selects for scope, symbol, source, and translation status.

- [ ] **Step 7: Implement refresh orchestration in `NewsPage`**

POST `{watchlistSymbols: symbols}` from `useWatchlist`; store returned run ID in component state; poll `/news/refresh/{id}` every 1.5 seconds only while non-terminal; on terminal state invalidate `['news-24h']` and `['news-24h-summary']`; keep feed data visible with `placeholderData` during refresh.

- [ ] **Step 8: Implement cursor Load More**

Use `useInfiniteQuery` with `nextCursor`; append pages while deduping by article ID; reset query key when URL filters change.

- [ ] **Step 9: Implement approved responsive styling**

Desktop grid: bounded left digest/filter column and flexible Timeline Feed. Mobile breakpoint stacks sections, makes chips horizontally scrollable inside their own container, and maintains document horizontal overflow at zero. Reuse current CSS variables and radii.

- [ ] **Step 10: Run component tests, typecheck, and build**

```bash
cd frontend
./node_modules/.bin/vitest run
./node_modules/.bin/tsc -b
./node_modules/.bin/vite build
./node_modules/.bin/oxlint
```

Expected: tests/build pass; no new lint errors.

- [ ] **Step 11: Commit**

```bash
git add frontend/src/features/news frontend/src/pages/NewsPage.tsx frontend/src/pages/NewsPage.test.tsx frontend/src/styles/index.css
git commit -m "feat: build Thai 24-hour news timeline"
```

---

### Task 9: Add End-to-End Coverage for Refresh and Fallbacks

**Files:**
- Modify: `frontend/e2e/smoke.spec.ts`
- Create: `frontend/e2e/fixtures/news.ts`

**Interfaces:**
- Consumes: complete backend/frontend contracts.
- Produces deterministic Playwright coverage independent of live providers.

- [ ] **Step 1: Create deterministic API fixtures**

Export ready, pending, fallback, partial-run, and empty feed JSON objects matching the exact frontend types. Include a logo URL intercepted by Playwright and four symbols to exercise `+1` ticker display.

- [ ] **Step 2: Add Timeline/filter E2E test**

Intercept `/api/news/24h*`, visit `/news`, assert heading/digest/timeline order, click Watchlist, assert URL `scope=watchlist`, and verify the next request contains the filter.

- [ ] **Step 3: Add manual Refresh E2E test**

Intercept POST refresh and successive status polls (`translating` then `completed`); assert the button disables, stage label changes, old article stays visible, and feed refetches after completion.

- [ ] **Step 4: Add fallback/error E2E test**

Assert partial warnings remain non-fatal, `failed` items show English and `รอแปล`, empty state contains no stale article, and original links use a new tab.

- [ ] **Step 5: Add mobile overflow test**

At 390×844 visit `/news`, verify digest precedes feed, filter chips remain usable, and `scrollWidth - clientWidth <= 1`.

- [ ] **Step 6: Run E2E suite**

Run: `cd frontend && ./node_modules/.bin/playwright test`  
Expected: all tests pass without depending on live news sources.

- [ ] **Step 7: Commit**

```bash
git add frontend/e2e/smoke.spec.ts frontend/e2e/fixtures/news.ts
git commit -m "test: cover news timeline refresh and fallbacks"
```

---

### Task 10: Operational Documentation and Final Verification

**Files:**
- Modify: `backend/.env.example`
- Modify: `frontend/README.md`
- Modify: `docs/project-status-and-next-steps.md`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: completed feature.
- Produces: documented setup, provider limitations, refresh behavior, and verified handoff.

- [ ] **Step 1: Add environment examples**

```dotenv
OPENSTOCK_NEWS_HTTP_TIMEOUT=15
OPENSTOCK_NEWS_MAX_FEED_BYTES=2000000
OPENSTOCK_NEWS_MAX_REDIRECTS=3
OPENSTOCK_NEWS_GOOGLE_FALLBACK_MIN_ITEMS=5
OPENSTOCK_NEWS_TRANSLATION_BATCH_SIZE=6
OPENSTOCK_NEWS_MAX_TRANSLATIONS_PER_REFRESH=48
OPENSTOCK_SEC_USER_AGENT=OpenStock your-email@example.com
```

Retain existing Gemini/OpenRouter settings; explicitly document that `OPENSTOCK_SEC_USER_AGENT` must contain a real contact before deployment.

- [ ] **Step 2: Document user behavior and limitations**

Explain manual refresh, 24-hour display window, 7-day retention, source list, AI routing, English fallback, no full-article scraping, no paywall bypass, and non-investment-advice disclaimer.

- [ ] **Step 3: Ignore runtime data**

Confirm SQLite files, cached feeds, cached logos, temporary downloads, test artifacts, and `.superpowers/` are excluded without ignoring source fixtures or docs.

- [ ] **Step 4: Run backend verification**

```bash
cd backend
uv sync --locked --group dev
uv run --locked --group dev pytest
```

Expected: all tests pass; no live provider calls occur in unit tests.

- [ ] **Step 5: Run frontend verification**

```bash
cd frontend
pnpm install --frozen-lockfile --config.minimumReleaseAge=0
./node_modules/.bin/vitest run
./node_modules/.bin/tsc -b
./node_modules/.bin/vite build
./node_modules/.bin/oxlint
./node_modules/.bin/playwright test
```

Expected: tests/build pass; no new lint errors; bundle-size advisory may remain documented.

- [ ] **Step 6: Run live smoke check manually**

Start backend/frontend, open `/news`, press Refresh once, and record source counts, translation provider counts, run status, console errors, and mobile overflow. Do not treat a provider outage as a code failure if the partial-warning/fallback path behaves as specified.

- [ ] **Step 7: Audit secrets and runtime files**

Run:

```bash
git status --short
git diff --check
git grep -n "GEMINI_API_KEY\|OPENROUTER_API_KEY\|FINNHUB_API_KEY\|ALPHAVANTAGE_API_KEY" -- ':!backend/.env.example'
```

Expected: no secret values or runtime binaries staged.

- [ ] **Step 8: Commit**

```bash
git add backend/.env.example frontend/README.md docs/project-status-and-next-steps.md .gitignore
git commit -m "docs: document 24-hour news feed operations"
```

- [ ] **Step 9: Prepare review summary**

Report changed files, verification results, known external-source limitations, and confirm that deployment/push require separate user approval.
