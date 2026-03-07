"""Integration tests for the pf_platform FastAPI endpoints."""

import io

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("starlette")
pytest.importorskip("slowapi")

# ---------------------------------------------------------------------------
# Minimal valid config + metrics for testing
# ---------------------------------------------------------------------------

MINIMAL_CONFIG = (
    b"meta:\n"
    b"  title: Test\n"
    b"theme:\n"
    b"  primary: '#1C2537'\n"
    b"  accent: '#C4A962'\n"
    b"  fonts:\n"
    b"    heading: Playfair Display\n"
    b"    body: Lato\n"
    b"slides:\n"
    b"  - layout: title\n"
    b"    data:\n"
    b"      title: Hello\n"
    b"  - layout: closing\n"
    b"    data:\n"
    b"      title: End\n"
)

MINIMAL_METRICS = b"{}"

INVALID_CONFIG = b"not: valid: yaml: config: missing slides\ntheme: {}\n"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """TestClient with STORE_DIR monkeypatched to tmp_path."""
    import pf_platform.storage as storage_mod
    from pf_platform.api import _mounted_decks

    monkeypatch.setattr(storage_mod, "STORE_DIR", tmp_path)
    _mounted_decks.clear()

    from starlette.testclient import TestClient
    from pf_platform.api import app

    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_deck(client, config_bytes=MINIMAL_CONFIG, metrics_bytes=MINIMAL_METRICS):
    """POST /api/build and return the JSON response body."""
    response = client.post(
        "/api/build",
        files={
            "config": ("presentation.yaml", io.BytesIO(config_bytes), "text/yaml"),
            "metrics": ("metrics.json", io.BytesIO(metrics_bytes), "application/json"),
        },
    )
    return response


# ---------------------------------------------------------------------------
# Build endpoint
# ---------------------------------------------------------------------------


def test_build_endpoint(client):
    """POST /api/build returns deck_id, shareable URL, and slide_count >= 2."""
    resp = _build_deck(client)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "deck_id" in data
    assert "/d/" in data["url"]
    assert "present.html" in data["url"]
    assert data["slide_count"] >= 2


def test_deck_served(client):
    """Built deck is accessible at the returned URL with HTML content."""
    build_resp = _build_deck(client)
    assert build_resp.status_code == 200
    url = build_resp.json()["url"]

    resp = client.get(url)
    assert resp.status_code == 200
    body = resp.text
    assert "<!DOCTYPE html>" in body or "<html" in body


def test_embed_headers(client):
    """Deck responses under /d/ include frame-ancestors CSP header."""
    build_resp = _build_deck(client)
    assert build_resp.status_code == 200
    url = build_resp.json()["url"]

    resp = client.get(url)
    assert resp.status_code == 200
    csp = resp.headers.get("content-security-policy", "")
    assert "frame-ancestors" in csp


def test_build_invalid_config(client, tmp_path, monkeypatch):
    """POST /api/build with malformed YAML returns 422."""
    import pf_platform.storage as storage_mod
    monkeypatch.setattr(storage_mod, "STORE_DIR", tmp_path)

    bad_config = b"slides: []\ntheme: null\n"  # invalid — missing required fields
    resp = _build_deck(client, config_bytes=bad_config)
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Embed endpoint
# ---------------------------------------------------------------------------


def test_embed_endpoint(client):
    """GET /api/decks/{deck_id}/embed returns iframe HTML."""
    build_resp = _build_deck(client)
    assert build_resp.status_code == 200
    deck_id = build_resp.json()["deck_id"]

    resp = client.get(f"/api/decks/{deck_id}/embed")
    assert resp.status_code == 200
    data = resp.json()
    assert "<iframe" in data["iframe_html"]
    assert deck_id in data["url"]


# ---------------------------------------------------------------------------
# Validate endpoint
# ---------------------------------------------------------------------------


def test_validate_endpoint_valid(client):
    """POST /api/validate with valid config returns valid: true, errors: []."""
    resp = client.post(
        "/api/validate",
        files={"config": ("presentation.yaml", io.BytesIO(MINIMAL_CONFIG), "text/yaml")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is True
    assert data["errors"] == []


def test_validate_endpoint_invalid(client):
    """POST /api/validate with invalid config returns valid: false and errors."""
    bad_config = b"theme:\n  primary: '#000'\n"  # missing slides
    resp = client.post(
        "/api/validate",
        files={"config": ("presentation.yaml", io.BytesIO(bad_config), "text/yaml")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is False
    assert len(data["errors"]) > 0


# ---------------------------------------------------------------------------
# Delete endpoint
# ---------------------------------------------------------------------------


def test_delete_deck(client):
    """DELETE /api/decks/{deck_id} removes the deck; second DELETE returns 404."""
    build_resp = _build_deck(client)
    assert build_resp.status_code == 200
    deck_id = build_resp.json()["deck_id"]

    # First delete: success
    resp = client.delete(f"/api/decks/{deck_id}")
    assert resp.status_code == 200

    # Second delete: not found
    resp = client.delete(f"/api/decks/{deck_id}")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------


def test_rate_limit(tmp_path, monkeypatch):
    """11 rapid POST /api/build requests triggers 429 on the 11th."""
    import pf_platform.storage as storage_mod
    from pf_platform.api import _mounted_decks, limiter, app

    monkeypatch.setattr(storage_mod, "STORE_DIR", tmp_path)
    _mounted_decks.clear()

    # Reset the rate limiter storage between test runs
    limiter._storage.reset()  # type: ignore[attr-defined]

    from starlette.testclient import TestClient

    with TestClient(app, raise_server_exceptions=False) as client:
        responses = []
        for _ in range(11):
            r = client.post(
                "/api/build",
                files={
                    "config": ("presentation.yaml", io.BytesIO(MINIMAL_CONFIG), "text/yaml"),
                    "metrics": ("metrics.json", io.BytesIO(MINIMAL_METRICS), "application/json"),
                },
            )
            responses.append(r.status_code)

    assert 429 in responses, f"Expected 429 in responses, got: {responses}"
