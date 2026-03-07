"""Tests for pf_platform analytics store and API endpoints."""

import sqlite3

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("starlette")
pytest.importorskip("slowapi")

# ---------------------------------------------------------------------------
# Unit tests — analytics.py
# ---------------------------------------------------------------------------


def test_init_db_creates_table(tmp_path):
    """init_db() creates the slide_events table."""
    from pf_platform.analytics import init_db

    db = tmp_path / "analytics.db"
    init_db(db)

    with sqlite3.connect(db) as conn:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='slide_events'"
        )
        assert cursor.fetchone() is not None, "slide_events table not created"


def test_record_event(tmp_path):
    """record_event() inserts rows into slide_events."""
    from pf_platform.analytics import init_db, record_event

    db = tmp_path / "analytics.db"
    init_db(db)
    record_event("deck-a", 1, 1000, db)
    record_event("deck-a", 2, 2000, db)
    record_event("deck-a", 3, 3000, db)

    with sqlite3.connect(db) as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM slide_events")
        assert cursor.fetchone()[0] == 3


def test_record_event_auto_inits(tmp_path):
    """record_event() works without a prior init_db() call — auto-creates the table."""
    from pf_platform.analytics import record_event

    db = tmp_path / "auto.db"
    # Do NOT call init_db() first
    record_event("deck-x", 1, 500, db)

    with sqlite3.connect(db) as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM slide_events")
        assert cursor.fetchone()[0] == 1


def test_get_dashboard_empty(tmp_path):
    """get_dashboard() returns empty list when no events exist for a deck."""
    from pf_platform.analytics import get_dashboard, init_db

    db = tmp_path / "analytics.db"
    init_db(db)
    result = get_dashboard("no-events-deck", db)
    assert result == []


def test_get_dashboard_aggregation(tmp_path):
    """get_dashboard() correctly aggregates views, total_ms, avg_ms per slide."""
    from pf_platform.analytics import get_dashboard, record_event

    db = tmp_path / "analytics.db"
    # Slide 1: 2 events of 1000ms and 2000ms
    record_event("deck-agg", 1, 1000, db)
    record_event("deck-agg", 1, 2000, db)
    # Slide 2: 1 event of 3000ms
    record_event("deck-agg", 2, 3000, db)

    result = get_dashboard("deck-agg", db)
    assert len(result) == 2

    slide1 = result[0]
    assert slide1["slide_idx"] == 1
    assert slide1["views"] == 2
    assert slide1["total_ms"] == 3000
    assert slide1["avg_ms"] == 1500.0

    slide2 = result[1]
    assert slide2["slide_idx"] == 2
    assert slide2["views"] == 1
    assert slide2["total_ms"] == 3000
    assert slide2["avg_ms"] == 3000.0


def test_get_dashboard_filters_by_deck(tmp_path):
    """get_dashboard() only returns events for the requested deck_id."""
    from pf_platform.analytics import get_dashboard, record_event

    db = tmp_path / "analytics.db"
    record_event("deck-a", 1, 1000, db)
    record_event("deck-a", 1, 2000, db)
    record_event("deck-b", 1, 9999, db)
    record_event("deck-b", 2, 9999, db)

    result_a = get_dashboard("deck-a", db)
    assert len(result_a) == 1
    assert result_a[0]["views"] == 2
    assert result_a[0]["total_ms"] == 3000

    result_b = get_dashboard("deck-b", db)
    assert len(result_b) == 2  # slide 1 and slide 2 from deck-b


def test_get_total_views(tmp_path):
    """get_total_views() returns total count of events for a deck."""
    from pf_platform.analytics import get_total_views, record_event

    db = tmp_path / "analytics.db"
    for i in range(5):
        record_event("deck-v", i + 1, 1000, db)

    assert get_total_views("deck-v", db) == 5


# ---------------------------------------------------------------------------
# Integration tests — API endpoints
# ---------------------------------------------------------------------------


@pytest.fixture()
def analytics_client(tmp_path, monkeypatch):
    """TestClient with analytics DB_PATH monkeypatched to tmp_path."""
    import pf_platform.analytics as analytics_mod
    import pf_platform.storage as storage_mod
    from pf_platform.api import _mounted_decks

    db_path = tmp_path / "analytics.db"
    monkeypatch.setattr(analytics_mod, "DB_PATH", db_path)
    monkeypatch.setattr(storage_mod, "STORE_DIR", tmp_path)
    _mounted_decks.clear()

    from starlette.testclient import TestClient
    from pf_platform.api import app

    with TestClient(app, raise_server_exceptions=True) as c:
        yield c, tmp_path, db_path


def test_events_endpoint(analytics_client):
    """POST /api/events records an event and returns 200 with status ok."""
    client, tmp_path, db_path = analytics_client

    import pf_platform.analytics as analytics_mod

    resp = client.post(
        "/api/events",
        json={"deck_id": "test-deck", "slide": 1, "duration_ms": 5000},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"status": "ok"}

    # Verify the event was persisted
    from pf_platform.analytics import get_total_views

    assert get_total_views("test-deck", db_path) == 1


def test_dashboard_endpoint(analytics_client):
    """GET /api/decks/{deck_id}/dashboard returns correct aggregations."""
    client, tmp_path, db_path = analytics_client

    from pf_platform.analytics import record_event

    # Seed events directly
    record_event("dash-deck", 1, 1000, db_path)
    record_event("dash-deck", 1, 2000, db_path)
    record_event("dash-deck", 2, 3000, db_path)

    resp = client.get("/api/decks/dash-deck/dashboard")
    assert resp.status_code == 200, resp.text

    data = resp.json()
    assert data["deck_id"] == "dash-deck"
    assert data["total_views"] == 3

    slides = data["slides"]
    assert len(slides) == 2

    s1 = slides[0]
    assert s1["slide"] == 1
    assert s1["views"] == 2
    assert s1["total_ms"] == 3000
    assert s1["avg_ms"] == 1500.0

    s2 = slides[1]
    assert s2["slide"] == 2
    assert s2["views"] == 1
    assert s2["total_ms"] == 3000
    assert s2["avg_ms"] == 3000.0


def test_events_invalid_payload(analytics_client):
    """POST /api/events with missing required fields returns 422."""
    client, tmp_path, db_path = analytics_client

    # Missing duration_ms
    resp = client.post(
        "/api/events",
        json={"deck_id": "test-deck", "slide": 1},
    )
    assert resp.status_code == 422

    # Completely empty body
    resp = client.post("/api/events", json={})
    assert resp.status_code == 422
