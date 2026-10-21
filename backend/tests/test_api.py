from fastapi.testclient import TestClient

from app.main import app
from app.routers import meta as meta_router
from app.services import search as search_service

client = TestClient(app)


def test_root_and_health(monkeypatch, db):
    monkeypatch.setattr(meta_router, "get_db", lambda: db)
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "OpenStock API"
    assert body["symbolCount"] == 30
    assert "gemini_api_key" not in response.text
    assert "GEMINI_API_KEY" not in response.text
    assert len(body["providers"]) == 5


def test_catalog_has_groups_and_ranges():
    response = client.get("/api/catalog")
    assert response.status_code == 200
    body = response.json()
    assert {g["key"] for g in body["groups"]} == {"broad", "sectors", "industries", "themes"}
    assert [r["key"] for r in body["ranges"]] == ["1d", "1w", "1mo", "3mo", "ytd"]
    assert body["benchmark"]["symbol"] == "SPY"
    assert "ไม่ใช่คำแนะนำการลงทุน" in body["disclaimer"]


def test_symbols_endpoint(monkeypatch, db):
    monkeypatch.setattr(meta_router, "get_db", lambda: db)
    response = client.get("/api/symbols?limit=30")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 30


def test_search_is_local_first(monkeypatch, db):
    monkeypatch.setattr(search_service, "get_db", lambda: db)

    async def no_remote(query, limit=8):
        return []

    monkeypatch.setattr(search_service.yahoo, "search", no_remote)
    response = client.get("/api/search?q=nvi")
    assert response.status_code == 200
    results = response.json()["results"]
    assert results[0]["symbol"] == "NVDA"
    assert results[0]["source"] == "local"


def test_openapi_available():
    response = client.get("/api/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    for path in (
        "/api/market/overview",
        "/api/flows",
        "/api/news/summary",
        "/api/symbol/{symbol}/levels",
        "/api/symbols",
    ):
        assert path in paths
