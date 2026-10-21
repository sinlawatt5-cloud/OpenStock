def test_seed_has_thirty_symbols(db):
    assert db.symbol_count() == 30
    items = db.list_symbols(30)
    assert items[0]["symbol"] == "AAPL"
    assert items[0]["name_th"] == "แอปเปิล"


def test_local_search_finds_nvda(db):
    results = db.search_symbols("nvi")
    assert results
    assert results[0]["symbol"] == "NVDA"


def test_peers_are_same_sector(db):
    peers = db.peers("Technology", "NVDA", limit=5)
    assert peers
    assert all(p["sector"] == "Technology" for p in peers)
    assert all(p["symbol"] != "NVDA" for p in peers)


def test_budget_cap(db):
    assert db.try_consume("alphavantage", cap=2) is True
    assert db.try_consume("alphavantage", cap=2) is True
    assert db.try_consume("alphavantage", cap=2) is False
    assert db.budget_used("alphavantage") == 2
