# Global Company Logo System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolve, validate, cache, serve, and display authentic company/ETF logos consistently across OpenStock with a safe initials fallback.

**Architecture:** Add a SQLite-backed logo registry and a backend resolver that prefers Yahoo profile data, then official-site icons, then a curated map. Cache validated images locally and expose them through one same-origin endpoint; enrich existing API responses with `logoUrl` and make the shared React `Avatar` component recover from broken images.

**Tech Stack:** Python 3.12, FastAPI, SQLite, httpx, pytest/respx, React 19, TypeScript, TanStack Query, Vitest/jsdom, Playwright.

**Spec:** `docs/superpowers/specs/2026-10-21-news-feed-and-logo-design.md`

## Global Constraints

- Preserve the existing light cream OpenStock theme; do not introduce a dark theme.
- Logo resolution order is Yahoo `logoUrl` → official website icon/manifest → curated map → initials.
- Only fetch HTTPS image URLs; reject loopback, link-local, private, multicast, and unspecified IP destinations.
- Validate content type, file signature, response size, and image dimensions before caching.
- Cached logo binaries live under backend local data storage and must not be committed to Git.
- Do not hotlink external logos from the frontend; use `/api/logos/{symbol}`.
- Do not alter logo colors or claim affiliation with companies.
- Index/commodity/crypto rows without a company logo use existing asset-type icons or initials.
- Existing API fields remain backward compatible; `logoUrl` is additive and nullable.
- Current workspace contains uncommitted risk-on changes. Before execution, preserve them in a commit/stash and execute from a branch/worktree that includes them; never discard them.
- Verification commands must use the repository environments: backend `uv run --locked --group dev pytest`; frontend binaries may be run from `node_modules/.bin` when the local pnpm `minimumReleaseAge` policy blocks script invocation.

---

## File Structure

### Backend

- Create `backend/app/services/logos.py` — URL safety checks, remote image validation, cache writes, resolution orchestration, API-facing metadata.
- Create `backend/app/routers/logos.py` — same-origin cached logo endpoint.
- Create `backend/app/data/logo_overrides.py` — audited curated mappings for Popular 30 and core ETFs only.
- Modify `backend/app/db.py` — `symbol_logos` schema and repository methods.
- Modify `backend/app/config.py` — logo cache path, byte/dimension limits, resolver TTL.
- Modify `backend/app/main.py` — register logo router.
- Modify `backend/app/services/search.py`, `movers.py`, `symbol.py`, `flows.py`, `catalog.py` — additive `logoUrl` enrichment.
- Modify `backend/app/routers/meta.py` — add logos to `/symbols`.
- Create `backend/tests/test_logos.py` — resolver/storage/security tests.
- Modify `backend/tests/test_api.py` — logo endpoint and additive contract tests.

### Frontend

- Modify `frontend/src/components/Avatar.tsx` — `onError` fallback and reset behavior.
- Modify `frontend/src/lib/types.ts` — nullable `logoUrl` fields.
- Modify `frontend/src/components/SearchDialog.tsx` — pass logo into `Avatar`.
- Modify `frontend/src/features/overview/MoversBoard.tsx` — use normalized `logoUrl`.
- Modify `frontend/src/pages/WatchlistPage.tsx` — use logos from symbols/search/history responses.
- Modify `frontend/src/pages/SymbolPage.tsx` — use same-origin logo and peer logos.
- Modify `frontend/src/pages/FlowsPage.tsx` — render ETF avatars where space permits.
- Create `frontend/src/components/Avatar.test.tsx` — image/fallback behavior.
- Modify `frontend/e2e/smoke.spec.ts` — global logo smoke coverage.

---

### Task 1: Add Logo Registry Storage

**Files:**
- Modify: `backend/app/db.py`
- Modify: `backend/app/config.py`
- Test: `backend/tests/test_logos.py`

**Interfaces:**
- Produces: `Database.logo_get(symbol: str) -> dict[str, Any] | None`
- Produces: `Database.logo_upsert(symbol: str, *, logo_path: str | None, source_url: str | None, logo_source: str | None, website: str | None, status: str, etag: str | None, content_type: str | None) -> None`
- Produces: `Settings.openstock_logo_cache_path`, `Settings.openstock_logo_max_bytes`, `Settings.openstock_logo_max_dimension`, `Settings.openstock_logo_ttl_seconds`

- [ ] **Step 1: Write failing database tests**

```python
# backend/tests/test_logos.py

def test_logo_registry_round_trip(db):
    db.logo_upsert(
        "NVDA",
        logo_path="NVDA.webp",
        source_url="https://www.nvidia.com/favicon.ico",
        logo_source="official_site",
        website="https://www.nvidia.com",
        status="ready",
        etag='"abc"',
        content_type="image/webp",
    )
    row = db.logo_get("nvda")
    assert row is not None
    assert row["symbol"] == "NVDA"
    assert row["status"] == "ready"
    assert row["logo_path"] == "NVDA.webp"


def test_logo_registry_upsert_replaces_stale_value(db):
    db.logo_upsert("AAPL", logo_path=None, source_url=None, logo_source=None,
                   website=None, status="failed", etag=None, content_type=None)
    db.logo_upsert("AAPL", logo_path="AAPL.png", source_url="https://apple.com/favicon.ico",
                   logo_source="official_site", website="https://apple.com",
                   status="ready", etag=None, content_type="image/png")
    assert db.logo_get("AAPL")["status"] == "ready"
```

- [ ] **Step 2: Run tests and confirm the missing-method failure**

Run: `cd backend && uv run --locked --group dev pytest tests/test_logos.py -v`  
Expected: FAIL because `logo_upsert`/`logo_get` do not exist.

- [ ] **Step 3: Extend `_SCHEMA` and implement repository methods**

Add:

```sql
CREATE TABLE IF NOT EXISTS symbol_logos (
    symbol TEXT PRIMARY KEY,
    logo_path TEXT,
    source_url TEXT,
    logo_source TEXT,
    website TEXT,
    status TEXT NOT NULL,
    etag TEXT,
    content_type TEXT,
    updated_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_symbol_logos_status_updated
ON symbol_logos(status, updated_at);
```

Normalize symbols with `symbol.strip().upper()` in both methods. Use this exact upsert shape and `time.time()` for `updated_at`:

```sql
INSERT INTO symbol_logos(
    symbol, logo_path, source_url, logo_source, website,
    status, etag, content_type, updated_at
) VALUES(?,?,?,?,?,?,?,?,?)
ON CONFLICT(symbol) DO UPDATE SET
    logo_path=excluded.logo_path,
    source_url=excluded.source_url,
    logo_source=excluded.logo_source,
    website=excluded.website,
    status=excluded.status,
    etag=excluded.etag,
    content_type=excluded.content_type,
    updated_at=excluded.updated_at
```

- [ ] **Step 4: Add settings with exact defaults**

```python
openstock_logo_cache_path: str = str(BASE_DIR / "data" / "logos")
openstock_logo_max_bytes: int = 1_500_000
openstock_logo_max_dimension: int = 2048
openstock_logo_ttl_seconds: int = 30 * 24 * 3600
```

- [ ] **Step 5: Run storage tests**

Run: `cd backend && uv run --locked --group dev pytest tests/test_logos.py -v`  
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/db.py backend/app/config.py backend/tests/test_logos.py
git commit -m "feat: add cached logo registry"
```

---

### Task 2: Implement Safe Logo Fetching and Resolution

**Files:**
- Create: `backend/app/data/logo_overrides.py`
- Create: `backend/app/services/logos.py`
- Modify: `backend/app/providers/yahoo.py`
- Test: `backend/tests/test_logos.py`

**Interfaces:**
- Consumes: `Database.logo_get`, `Database.logo_upsert`, logo settings from Task 1.
- Produces: `async resolve_logo(symbol: str, *, website: str | None = None, candidate_url: str | None = None, force: bool = False) -> dict[str, Any]`
- Produces: `logo_api_url(symbol: str, status: str | None = None) -> str | None`
- Produces: `async yahoo.logo_candidates(symbol: str) -> dict[str, str | None]`

- [ ] **Step 1: Write failing security and cache tests**

Use `respx` to cover:

```python
@pytest.mark.asyncio
async def test_resolver_rejects_private_destination(monkeypatch, db, tmp_path):
    monkeypatch.setattr(logos, "get_db", lambda: db)
    result = await logos.resolve_logo("TEST", candidate_url="http://127.0.0.1/logo.png")
    assert result["status"] == "failed"
    assert db.logo_get("TEST")["logo_path"] is None


@pytest.mark.asyncio
async def test_resolver_caches_valid_png(monkeypatch, db, tmp_path, respx_mock):
    configure_logo_path(monkeypatch, tmp_path)
    monkeypatch.setattr(logos, "get_db", lambda: db)
    respx_mock.get("https://cdn.example.com/aapl.png").respond(
        200, content=ONE_PIXEL_PNG, headers={"content-type": "image/png"}
    )
    result = await logos.resolve_logo("AAPL", candidate_url="https://cdn.example.com/aapl.png")
    assert result["status"] == "ready"
    assert result["logoUrl"] == "/api/logos/AAPL"
    assert (tmp_path / result["logoPath"]).exists()
```

Also test oversized bodies, non-image MIME, invalid signature, redirects to private IP, and TTL cache reuse without a second HTTP request.

- [ ] **Step 2: Run tests and verify failure**

Run: `cd backend && uv run --locked --group dev pytest tests/test_logos.py -v`  
Expected: FAIL because `services.logos` does not exist.

- [ ] **Step 3: Create audited curated mappings**

```python
# backend/app/data/logo_overrides.py
LOGO_OVERRIDES: dict[str, dict[str, str]] = {
    "AAPL": {"website": "https://www.apple.com"},
    "MSFT": {"website": "https://www.microsoft.com"},
    "NVDA": {"website": "https://www.nvidia.com"},
}
```

Populate the exact 30 symbols from `SEED_SYMBOLS` plus core ETFs from `GROUPS`. Store official websites, not unaudited third-party logo URLs.

- [ ] **Step 4: Implement network safety helpers**

In `services/logos.py` add focused functions:

```python
def normalize_symbol(symbol: str) -> str:
    value = symbol.strip().upper()
    if not re.fullmatch(r"[A-Z0-9.-]{1,12}", value):
        raise ValueError("invalid symbol")
    return value


def is_public_address(address: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return not any((
        address.is_private,
        address.is_loopback,
        address.is_link_local,
        address.is_multicast,
        address.is_reserved,
        address.is_unspecified,
    ))


async def resolve_public_addresses(hostname: str) -> list[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    infos = await asyncio.get_running_loop().getaddrinfo(hostname, 443, type=socket.SOCK_STREAM)
    addresses = list({ipaddress.ip_address(info[4][0]) for info in infos})
    if not addresses or not all(is_public_address(address) for address in addresses):
        raise ValueError("hostname does not resolve exclusively to public addresses")
    return addresses


def sniff_image_type(data: bytes) -> str | None:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith((b"RIFF",)) and data[8:12] == b"WEBP":
        return "image/webp"
    if data.startswith(b"\x00\x00\x01\x00"):
        return "image/x-icon"
    return None


def logo_api_url(symbol: str, status: str | None = None) -> str | None:
    return f"/api/logos/{normalize_symbol(symbol)}" if status == "ready" else None
```

Use `urllib.parse`, `ipaddress`, and async DNS resolution. Reject any resolved address where `is_private`, `is_loopback`, `is_link_local`, `is_multicast`, `is_reserved`, or `is_unspecified` is true. Re-check every redirect target; allow at most three redirects.

- [ ] **Step 5: Implement bounded image download**

Stream with `httpx.AsyncClient`, stop after `openstock_logo_max_bytes`, accept PNG/JPEG/WebP/ICO signatures, and write atomically via a temporary file followed by `Path.replace`. Do not render SVG from untrusted sources in v1.

- [ ] **Step 6: Implement candidate discovery and resolution order**

`yahoo.logo_candidates` should return Yahoo profile `logo` and `website`. For official websites, request only the homepage and parse `<link rel="icon">`/`<link rel="apple-touch-icon">` with a bounded regex/HTML parser; fall back to `/favicon.ico`. Resolution order must exactly match the spec. Save failures with status `failed` and a timestamp so they respect TTL before retrying.

- [ ] **Step 7: Run resolver tests**

Run: `cd backend && uv run --locked --group dev pytest tests/test_logos.py -v`  
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add backend/app/data/logo_overrides.py backend/app/services/logos.py backend/app/providers/yahoo.py backend/tests/test_logos.py
git commit -m "feat: safely resolve and cache company logos"
```

---

### Task 3: Serve Cached Logos Through FastAPI

**Files:**
- Create: `backend/app/routers/logos.py`
- Modify: `backend/app/main.py`
- Modify: `backend/tests/test_api.py`

**Interfaces:**
- Consumes: registry and cache files from Tasks 1–2.
- Produces: `GET /api/logos/{symbol}` returning a validated cached file with `ETag` and long-lived cache headers.

- [ ] **Step 1: Add failing API tests**

```python
def test_cached_logo_endpoint(monkeypatch, db, tmp_path):
    path = tmp_path / "NVDA.png"
    path.write_bytes(ONE_PIXEL_PNG)
    db.logo_upsert("NVDA", logo_path="NVDA.png", source_url="https://example.com/n.png",
                   logo_source="official_site", website="https://nvidia.com",
                   status="ready", etag='"logo-etag"', content_type="image/png")
    monkeypatch.setattr(logos_router, "get_db", lambda: db)
    monkeypatch.setattr(logos_router, "logo_cache_dir", lambda: tmp_path)
    response = client.get("/api/logos/NVDA")
    assert response.status_code == 200
    assert response.headers["etag"] == '"logo-etag"'
    assert "max-age=" in response.headers["cache-control"]
    assert response.content == ONE_PIXEL_PNG


def test_missing_logo_returns_404(monkeypatch, db):
    monkeypatch.setattr(logos_router, "get_db", lambda: db)
    assert client.get("/api/logos/UNKNOWN").status_code == 404
```

- [ ] **Step 2: Run targeted tests and verify missing route**

Run: `cd backend && uv run --locked --group dev pytest tests/test_api.py -k logo -v`  
Expected: FAIL with 404 for the cached logo case.

- [ ] **Step 3: Implement route with safe path resolution**

Use a strict ticker regex `^[A-Z0-9.-]{1,12}$`, look up the database row, resolve `(cache_dir / logo_path).resolve()`, and verify it remains inside `cache_dir.resolve()` before returning `FileResponse`. Never accept a filesystem path from the request.

- [ ] **Step 4: Register router in `main.py`**

Import `logos` from routers and include it with the existing `/api` prefix.

- [ ] **Step 5: Run API and OpenAPI tests**

Run: `cd backend && uv run --locked --group dev pytest tests/test_api.py -v`  
Expected: PASS; OpenAPI includes `/api/logos/{symbol}`.

- [ ] **Step 6: Commit**

```bash
git add backend/app/routers/logos.py backend/app/main.py backend/tests/test_api.py
git commit -m "feat: serve cached logos from same-origin API"
```

---

### Task 4: Enrich Existing Backend Responses With `logoUrl`

**Files:**
- Modify: `backend/app/services/logos.py`
- Modify: `backend/app/services/search.py`
- Modify: `backend/app/services/movers.py`
- Modify: `backend/app/services/symbol.py`
- Modify: `backend/app/services/flows.py`
- Modify: `backend/app/services/catalog.py`
- Modify: `backend/app/routers/meta.py`
- Modify: `backend/tests/test_api.py`
- Modify: `backend/tests/test_flows.py`

**Interfaces:**
- Consumes: `logo_api_url(symbol, status)` from Task 2.
- Produces: nullable `logoUrl` on symbol/search/mover/profile/peer/flow/catalog items.

- [ ] **Step 1: Add contract tests for additive fields**

Add assertions that `/api/symbols`, local search, movers, symbol profile peers, and flow rows include a `logoUrl` key. Seed a ready logo for one symbol and assert its value is `/api/logos/NVDA`; assert unresolved symbols return `None`.

- [ ] **Step 2: Run contract tests and verify failures**

Run: `cd backend && uv run --locked --group dev pytest tests/test_api.py tests/test_flows.py -v`  
Expected: FAIL on missing `logoUrl`.

- [ ] **Step 3: Add a side-effect-free lookup helper**

```python
def cached_logo_url(symbol: str, db: Database | None = None) -> str | None:
    row = (db or get_db()).logo_get(symbol)
    return logo_api_url(symbol, row.get("status") if row else None)
```

Response construction must not trigger network resolution. Resolution occurs during profile/news refresh flows only.

- [ ] **Step 4: Enrich every response**

Add `logoUrl` without removing existing `logo` fields. For symbol profile responses, prefer same-origin `logoUrl` while retaining provider `logo` internally. For `flows.py`, enrich ETF rows after `_row_for`; for `catalog.py`, return copied item dictionaries so static globals are never mutated.

- [ ] **Step 5: Run backend suite**

Run: `cd backend && uv run --locked --group dev pytest`  
Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services backend/app/routers/meta.py backend/tests
git commit -m "feat: expose cached logo URLs across APIs"
```

---

### Task 5: Make the Shared Avatar Fail Safe

**Files:**
- Modify: `frontend/src/components/Avatar.tsx`
- Modify: `frontend/src/lib/types.ts`
- Create: `frontend/src/components/Avatar.test.tsx`

**Interfaces:**
- Consumes: nullable same-origin `logoUrl` fields from Task 4.
- Produces: `<Avatar symbol name logo>` that shows an image when healthy and initials after an image error; resets when `logo` or `symbol` changes.

- [ ] **Step 1: Write failing component tests**

```tsx
// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import { Avatar } from './Avatar'

afterEach(cleanup)

describe('Avatar', () => {
  it('shows a provided logo', () => {
    render(<Avatar symbol="NVDA" logo="/api/logos/NVDA" />)
    expect(screen.getByRole('img')).toHaveAttribute('src', '/api/logos/NVDA')
  })

  it('falls back to initials when the image fails', () => {
    render(<Avatar symbol="NVDA" logo="/api/logos/NVDA" />)
    fireEvent.error(screen.getByRole('img'))
    expect(screen.queryByRole('img')).toBeNull()
    expect(screen.getByText('NV')).toBeTruthy()
  })
})
```

If jest-dom matchers are not configured, assert with `getAttribute('src')` instead of `toHaveAttribute`.

- [ ] **Step 2: Run the test and verify failure**

Run: `cd frontend && ./node_modules/.bin/vitest run src/components/Avatar.test.tsx`  
Expected: FAIL because the broken image remains rendered.

- [ ] **Step 3: Implement error state with reset**

Use `useEffect(() => setFailed(false), [logo, symbol])`; render the image only when `logo && !failed`; set `failed` in `onError`. Preserve `loading="lazy"`, `referrerPolicy="no-referrer"`, and decorative empty `alt`.

- [ ] **Step 4: Add nullable `logoUrl` to shared types**

Update `MoverRow`, `FlowRow`, `HistoryResponse`, `Quote`, `Profile`, `Peer`, `SymbolItem`, search result items, and catalog group items. Keep legacy `logo?: string | null` only where the backend still emits it.

- [ ] **Step 5: Run frontend unit tests**

Run: `cd frontend && ./node_modules/.bin/vitest run`  
Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/Avatar.tsx frontend/src/components/Avatar.test.tsx frontend/src/lib/types.ts
git commit -m "feat: add resilient shared stock avatar"
```

---

### Task 6: Roll Logos Out Across the Existing UI

**Files:**
- Modify: `frontend/src/components/SearchDialog.tsx`
- Modify: `frontend/src/features/overview/MoversBoard.tsx`
- Modify: `frontend/src/pages/WatchlistPage.tsx`
- Modify: `frontend/src/pages/SymbolPage.tsx`
- Modify: `frontend/src/pages/FlowsPage.tsx`
- Modify: `frontend/src/styles/index.css`
- Modify: `frontend/e2e/smoke.spec.ts`

**Interfaces:**
- Consumes: `logoUrl` response fields and resilient `Avatar` from Task 5.
- Produces: consistent logos in search, movers, watchlist, symbol header/peers, and ETF flows.

- [ ] **Step 1: Add E2E assertions before changing UI**

Extend fixtures/live smoke behavior to assert the target locations render either an `img` or visible initials; use locators on the Avatar container, not a specific provider logo that may be unavailable. Add a browser route override for `/api/logos/NVDA` returning a one-pixel PNG so one test deterministically verifies image rendering.

- [ ] **Step 2: Run targeted E2E and verify at least one failure**

Run: `cd frontend && ./node_modules/.bin/playwright test -g "logo"`  
Expected: FAIL because search/watchlist do not pass `logoUrl` yet.

- [ ] **Step 3: Pass `logoUrl` in every Avatar call**

Examples:

```tsx
<Avatar symbol={row.symbol} name={row.name} logo={row.logoUrl} />
<Avatar symbol={symbol} name={name} logo={profile?.logoUrl} className="avatar symbol-avatar" />
```

For Watchlist history responses, use `history.data?.logoUrl`. Update mapped search-result objects to retain `logoUrl`; do not drop it in `useMemo`.

- [ ] **Step 4: Add compact ETF avatars to flow rows**

Extend `FlowBar` to render a small Avatar beside the ETF name without reducing the bar area below usable width. At mobile breakpoints, keep the logo and ticker but allow the Thai label to ellipsize.

- [ ] **Step 5: Add peer logos in Symbol page**

Pass `peer.logoUrl` to Avatar in the peer list. Do not add extra profile requests per peer.

- [ ] **Step 6: Run frontend verification**

Run:

```bash
cd frontend
./node_modules/.bin/vitest run
./node_modules/.bin/tsc -b
./node_modules/.bin/vite build
./node_modules/.bin/oxlint
./node_modules/.bin/playwright test
```

Expected: tests/build pass; no new lint errors; existing warnings are recorded but not expanded.

- [ ] **Step 7: Run full backend verification**

Run: `cd backend && uv run --locked --group dev pytest`  
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add frontend/src frontend/e2e/smoke.spec.ts
git commit -m "feat: show authentic logos across OpenStock"
```

---

### Task 7: Document Logo Operations and Final Verification

**Files:**
- Modify: `backend/.env.example`
- Modify: `docs/project-status-and-next-steps.md`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: completed logo system.
- Produces: operator-visible cache configuration and documented maintenance behavior.

- [ ] **Step 1: Add environment examples**

```dotenv
OPENSTOCK_LOGO_CACHE_PATH=./data/logos
OPENSTOCK_LOGO_MAX_BYTES=1500000
OPENSTOCK_LOGO_MAX_DIMENSION=2048
OPENSTOCK_LOGO_TTL_SECONDS=2592000
```

- [ ] **Step 2: Ignore runtime assets**

Add `backend/data/logos/` and temporary logo download patterns to `.gitignore`. Confirm `.env` remains ignored.

- [ ] **Step 3: Document source order, fallback, and cleanup**

Update the project status document with endpoint, storage path, refresh TTL, security restrictions, and the rule that unresolved logos display initials.

- [ ] **Step 4: Run final verification**

```bash
cd backend && uv run --locked --group dev pytest
cd ../frontend && ./node_modules/.bin/vitest run
./node_modules/.bin/tsc -b
./node_modules/.bin/vite build
./node_modules/.bin/oxlint
./node_modules/.bin/playwright test
cd .. && git diff --check
```

Expected: all tests/build pass, no diff whitespace errors, no logo binaries or secrets in `git status`.

- [ ] **Step 5: Commit**

```bash
git add backend/.env.example .gitignore docs/project-status-and-next-steps.md
git commit -m "docs: document logo cache operations"
```
