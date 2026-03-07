# Phase 4: Hosted Platform - Research

**Researched:** 2026-03-07
**Domain:** FastAPI platform service, file hosting, WebSocket sync, analytics beacons, REST API, base-URL path abstraction
**Confidence:** HIGH (FastAPI, WebSocket patterns, and browser beacon API verified via official docs and current sources)

## Summary

Phase 4 adds a hosted-platform layer on top of the existing `PresentationBuilder`. The six requirements break into three distinct sub-problems: (1) asset path abstraction (`--base-url` in the CLI, PLAT-06), (2) a FastAPI service that accepts uploads, stores decks by UUID, and serves them publicly (PLAT-01, PLAT-02, PLAT-05), and (3) two real-time features baked into the viewer's JavaScript — an analytics beacon that fires on slide change and page-leave, and a WebSocket that syncs a presenter's slide position to all viewers (PLAT-03, PLAT-04).

The existing `PresentationBuilder.build()` writes all asset paths as relative strings (`theme/variables.css`, `slide_01.html`). Adding a `base_url` parameter requires a single pass over the rendered HTML to rewrite relative references to absolute ones — no Jinja2 template changes are needed. The FastAPI platform service is a standalone module (`platform/api.py`) that wraps the existing build pipeline, stores results in a `data/` directory keyed by UUID, and mounts the deck directories as `StaticFiles`. Rate limiting uses `slowapi` (the de-facto Starlette/FastAPI rate limiter). Analytics use `navigator.sendBeacon()` from the viewer JS hitting a `/api/events` endpoint that writes to SQLite. The presenter WebSocket uses a room-based in-memory `ConnectionManager` with last-writer-wins semantics — the server stores the current slide index per deck UUID and broadcasts any position change to all room members.

The existing test infrastructure uses `pytest` + `tmp_path`. New platform tests will use `httpx.AsyncClient` with `app` as the ASGI target (FastAPI's recommended testing pattern), plus a WebSocket client helper from `httpx-ws` or `starlette.testclient`.

**Primary recommendation:** Build `platform/` as a self-contained FastAPI sub-application with five modules: `api.py` (routes), `storage.py` (UUID + file ops), `worker.py` (build job), `analytics.py` (SQLite events), and `sync.py` (WebSocket room manager). Wire it into `pf/cli.py` with a `pf platform serve` sub-command.

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PLAT-01 | User can upload or link a deck to get a shareable URL with full navigator experience | FastAPI `UploadFile` multipart endpoint stores zip/files under `data/{uuid}/`; `StaticFiles` mounts at `/d/{uuid}/`; returns `{"url": "/d/{uuid}/present.html"}` |
| PLAT-02 | User can embed presentations via iframe or script tag in blogs, Notion, and docs | Platform returns an iframe snippet; `frame-ancestors *` CSP header on served deck HTML enables cross-origin embedding; `X-Frame-Options` must NOT be set |
| PLAT-03 | Platform tracks presentation analytics (views, slide-level engagement, time-per-slide) | `navigator.sendBeacon()` on `visibilitychange` + slide navigation events hits `/api/events`; SQLite stores `(deck_id, slide_idx, duration_ms, ts)`; dashboard endpoint aggregates |
| PLAT-04 | Multiple users can edit/follow the same presentation with real-time WebSocket sync | Room-based `ConnectionManager` at `/ws/{deck_id}`; server stores `current_slide` per room; any `{"slide": N}` message triggers last-writer-wins broadcast to all room members |
| PLAT-05 | REST API provides HTTP endpoints for build, validate, and generate operations | FastAPI routes: `POST /api/build`, `POST /api/validate`, `POST /api/generate`; `slowapi` rate limits; Pydantic response models for OpenAPI auto-docs |
| PLAT-06 | Build output supports configurable base URL for CDN/hosted asset paths (`--base-url`) | `PresentationBuilder.build(base_url=...)` rewrites relative hrefs/srcs in rendered HTML; CLI `pf build --base-url <url>` passes it through |
</phase_requirements>

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| fastapi | >=0.110 | Platform HTTP + WebSocket server | Async-native, OpenAPI auto-docs, in-process StaticFiles mount |
| uvicorn | >=0.27 | ASGI server for `pf platform serve` | FastAPI's recommended server; `--reload` for dev |
| python-multipart | >=0.0.9 | Multipart form/file upload parsing | Required by FastAPI for `UploadFile` endpoints |
| slowapi | >=0.1.9 | Request rate limiting for `/api/*` endpoints | De-facto Starlette/FastAPI limiter; decorator syntax; in-memory or Redis backend |
| httpx | >=0.27 | Async HTTP client for tests (`AsyncClient(app=...)`) | FastAPI's own test docs recommend it; replaces `requests` for async |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| starlette | (comes with fastapi) | `StaticFiles`, `WebSocket`, test client | Already a transitive dep |
| sqlite3 | stdlib | Analytics event store | Zero-dep, embedded, sufficient for v1 analytics volume |
| uuid | stdlib | Generate deck identifiers | `uuid.uuid4()` for unguessable deck IDs |
| shortuuid | >=1.0 | Optional short URL-safe deck IDs | If 36-char UUIDs are too long for share URLs |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| sqlite3 | PostgreSQL / SQLAlchemy | PostgreSQL requires infra; SQLite is zero-config for v1 |
| slowapi | Custom middleware | slowapi is maintained, handles edge cases; custom = maintenance burden |
| StaticFiles mount | Nginx / S3 | External services add infra; StaticFiles sufficient for v1 self-hosted |
| in-memory WebSocket room | Redis PubSub | Redis needed only for multi-process; single-process uvicorn is fine for v1 |

**Installation:**
```bash
pip install "presentation-framework[platform]"
# setup.py extras_require:
# "platform": ["fastapi>=0.110", "uvicorn>=0.27", "python-multipart>=0.0.9", "slowapi>=0.1.9", "httpx>=0.27"]
```

---

## Architecture Patterns

### Recommended Project Structure
```
platform/
├── __init__.py
├── api.py           # FastAPI app, routes, CORS, rate limiter wiring
├── storage.py       # UUID generation, directory layout, file I/O
├── worker.py        # Synchronous build job (calls PresentationBuilder)
├── analytics.py     # SQLite event store, aggregation queries
└── sync.py          # WebSocket ConnectionManager (room-based)
tests/
├── test_platform_api.py        # httpx AsyncClient tests for all HTTP routes
├── test_platform_analytics.py  # analytics store insert + aggregate
└── test_platform_sync.py       # WebSocket room broadcast tests
```

### Pattern 1: File Upload + Build Job
**What:** Accept `presentation.yaml` + `metrics.json` as multipart form fields. Read file bytes immediately inside the endpoint (before any `BackgroundTasks` run) to avoid the FastAPI v0.106+ UploadFile-close-before-background-task bug. Store the bytes, then run the build synchronously or pass bytes to `BackgroundTasks`.

**When to use:** POST /api/build, POST /upload

**Example:**
```python
# Source: https://fastapi.tiangolo.com/tutorial/request-files/
from fastapi import FastAPI, UploadFile, BackgroundTasks
import uuid, shutil
from pathlib import Path

STORE = Path("data")

@app.post("/api/build")
async def build(
    config: UploadFile,
    metrics: UploadFile,
    background_tasks: BackgroundTasks,
):
    deck_id = str(uuid.uuid4())
    deck_dir = STORE / deck_id
    deck_dir.mkdir(parents=True)

    # Read bytes NOW, inside endpoint body — avoids UploadFile-closed-in-BG-task bug
    config_bytes = await config.read()
    metrics_bytes = await metrics.read()

    (deck_dir / "presentation.yaml").write_bytes(config_bytes)
    (deck_dir / "metrics.json").write_bytes(metrics_bytes)

    background_tasks.add_task(run_build, deck_id, deck_dir)
    return {"deck_id": deck_id, "url": f"/d/{deck_id}/present.html"}

def run_build(deck_id: str, deck_dir: Path):
    from pf.builder import PresentationBuilder
    builder = PresentationBuilder(
        config_path=str(deck_dir / "presentation.yaml"),
        metrics_path=str(deck_dir / "metrics.json"),
    )
    builder.build(output_dir=str(deck_dir / "slides"))
```

### Pattern 2: StaticFiles Mount for Deck Serving (PLAT-01, PLAT-02)
**What:** After build completes, mount the slides output directory as a `StaticFiles` sub-application. Use `html=True` so `present.html` is served at the root path of the mount.

**When to use:** After deck upload/build succeeds; the mounted path becomes the shareable URL.

**Example:**
```python
# Source: https://fastapi.tiangolo.com/tutorial/static-files/
from fastapi.staticfiles import StaticFiles

def mount_deck(app, deck_id: str, slides_dir: Path):
    app.mount(
        f"/d/{deck_id}",
        StaticFiles(directory=str(slides_dir), html=True),
        name=f"deck-{deck_id}",
    )
```

**Critical for iframe embedding (PLAT-02):** Add these response headers to all `/d/{deck_id}/` responses:
- `Content-Security-Policy: frame-ancestors *` — allows cross-origin iframe embedding
- Do NOT set `X-Frame-Options: DENY` — that header blocks all embedding

```python
from starlette.middleware.base import BaseHTTPMiddleware

class EmbedHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/d/"):
            response.headers["Content-Security-Policy"] = "frame-ancestors *"
        return response
```

The iframe snippet to show users:
```html
<iframe
  src="https://your-platform.com/d/{deck_id}/present.html"
  width="1280"
  height="720"
  allowfullscreen
  style="border:none;max-width:100%;aspect-ratio:16/9;"
></iframe>
```

### Pattern 3: Rate Limiting with SlowAPI (PLAT-05)
**What:** `slowapi` wraps `limits` library with a decorator-based API. The `request` parameter must be explicitly declared in the endpoint signature.

**When to use:** Apply to all `/api/*` write endpoints. Public deck viewer (`/d/`) does not need rate limiting.

**Example:**
```python
# Source: https://slowapi.readthedocs.io/
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/build")
@limiter.limit("10/minute")
async def build(request: Request, config: UploadFile, metrics: UploadFile):
    ...
```

Note: `request: Request` must appear as the FIRST parameter after `self` (if any).

### Pattern 4: WebSocket Room Sync (PLAT-04)
**What:** In-memory `ConnectionManager` with a dict of `room_id -> set[WebSocket]`. Server stores canonical `current_slide` per room. Any client sending `{"slide": N}` triggers last-writer-wins: server updates stored state and broadcasts to all room members (including sender, so they get confirmation).

**When to use:** `GET /ws/{deck_id}` — one room per deck UUID.

**Example:**
```python
# Source: https://fastapi.tiangolo.com/advanced/websockets/
# + room pattern from https://blog.greeden.me/en/2025/10/28/...
import json
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    def __init__(self):
        self.rooms: Dict[str, Set[WebSocket]] = {}
        self.state: Dict[str, int] = {}  # deck_id -> current_slide (last-writer-wins)

    async def connect(self, deck_id: str, ws: WebSocket):
        await ws.accept()
        self.rooms.setdefault(deck_id, set()).add(ws)
        # Send current state to new joiner
        slide = self.state.get(deck_id, 1)
        await ws.send_json({"slide": slide, "type": "sync"})

    def disconnect(self, deck_id: str, ws: WebSocket):
        self.rooms.get(deck_id, set()).discard(ws)

    async def broadcast(self, deck_id: str, message: dict):
        for ws in list(self.rooms.get(deck_id, set())):
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(deck_id, ws)

manager = ConnectionManager()

@app.websocket("/ws/{deck_id}")
async def presenter_sync(websocket: WebSocket, deck_id: str):
    await manager.connect(deck_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            if "slide" in data:
                manager.state[deck_id] = data["slide"]  # last-writer-wins
                await manager.broadcast(deck_id, {"slide": data["slide"], "type": "goto"})
    except WebSocketDisconnect:
        manager.disconnect(deck_id, websocket)
```

**Client-side wiring in present.html.j2 (when `sync_url` template var is set):**
```javascript
// Added to present.html.j2 when platform-hosted
if (window.__PF_SYNC_URL) {
  const ws = new WebSocket(window.__PF_SYNC_URL);
  ws.onmessage = (e) => {
    const msg = JSON.parse(e.data);
    if (msg.type === 'goto') show(msg.slide, true);
  };
  // Hook into show() to broadcast
  const _origShow = show;
  window.show = function(n, instant, allFrags) {
    _origShow(n, instant, allFrags);
    ws.send(JSON.stringify({slide: n}));
  };
}
```

### Pattern 5: Analytics Beacon (PLAT-03)
**What:** JavaScript fires `navigator.sendBeacon()` on `visibilitychange` (MDN-recommended over `beforeunload`) and on each slide navigation event. Beacon hits `POST /api/events`. Platform stores events in SQLite table `slide_events(deck_id, slide_idx, duration_ms, ts)`. Dashboard aggregates per-slide totals.

**When to use:** Inject beacon script into `present.html.j2` when `analytics_url` template var is set.

**Example — Client (present.html.j2 addition):**
```javascript
// Slide analytics beacon
if (window.__PF_ANALYTICS_URL) {
  let slideStart = Date.now();
  let currentSlide = 1;

  function sendEvent(slideIdx, durationMs) {
    navigator.sendBeacon(
      window.__PF_ANALYTICS_URL,
      new Blob([JSON.stringify({
        deck_id: window.__PF_DECK_ID,
        slide: slideIdx,
        duration_ms: durationMs,
      })], {type: 'application/json'})
    );
  }

  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'hidden') {
      sendEvent(currentSlide, Date.now() - slideStart);
    }
  });

  // Intercept show() calls to track slide dwell time
  const _origShow = show;
  window.show = function(n, instant, allFrags) {
    const elapsed = Date.now() - slideStart;
    sendEvent(currentSlide, elapsed);
    currentSlide = n;
    slideStart = Date.now();
    _origShow(n, instant, allFrags);
  };
}
```

**Example — Server (analytics.py):**
```python
import sqlite3
from pathlib import Path

DB_PATH = Path("data/analytics.db")

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS slide_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deck_id TEXT NOT NULL,
                slide_idx INTEGER NOT NULL,
                duration_ms INTEGER NOT NULL,
                ts REAL DEFAULT (unixepoch('now', 'subsec'))
            )
        """)

def record_event(deck_id: str, slide_idx: int, duration_ms: int):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO slide_events (deck_id, slide_idx, duration_ms) VALUES (?,?,?)",
            (deck_id, slide_idx, duration_ms)
        )

def get_dashboard(deck_id: str) -> list[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("""
            SELECT slide_idx,
                   COUNT(*) as views,
                   SUM(duration_ms) as total_ms,
                   AVG(duration_ms) as avg_ms
            FROM slide_events
            WHERE deck_id = ?
            GROUP BY slide_idx
            ORDER BY slide_idx
        """, (deck_id,)).fetchall()
    return [{"slide": r[0], "views": r[1], "total_ms": r[2], "avg_ms": r[3]} for r in rows]
```

### Pattern 6: --base-url Path Rewriting (PLAT-06)
**What:** `PresentationBuilder.build()` accepts a `base_url: str | None = None` parameter. After all HTML files are written, a post-process pass rewrites relative hrefs and srcs to absolute URLs.

**When to use:** `pf build --base-url https://cdn.example.com/decks/abc123` and in the platform worker when building for hosted serving.

**Key insight:** The build currently writes these relative paths:
- `<link rel="stylesheet" href="theme/variables.css"/>` in `base.html.j2`
- `<link rel="stylesheet" href="theme/base.css"/>` in `base.html.j2`
- `<iframe src="{{ slides[0] }}">` in `present.html.j2` (references `slide_01.html` etc.)
- Plugin CSS paths like `theme/plugins/myplugin.css`

The rewriter must handle `href="theme/`, `href="slide_`, `src="slide_` patterns. A targeted regex rewrite is simpler than template parameterization because it keeps templates unchanged.

**Example — builder.py addition:**
```python
import re

def _rewrite_asset_paths(html: str, base_url: str) -> str:
    """Rewrite relative asset refs (href/src) to absolute base_url-prefixed paths."""
    base = base_url.rstrip("/")
    # Match href="relative/path" and src="relative/path" (not http/https/data)
    def make_absolute(m):
        attr, quote, path = m.group(1), m.group(2), m.group(3)
        if path.startswith(("http://", "https://", "data:", "//", "#")):
            return m.group(0)
        return f'{attr}={quote}{base}/{path}{quote}'
    return re.sub(r'(href|src)=(["\'])(?!http|https|data:|//|#)([^"\']+)\2', make_absolute, html)

# In PresentationBuilder.build():
def build(self, output_dir: str = "slides", base_url: str | None = None) -> Path:
    ...
    # After all files written:
    if base_url:
        for html_file in out.glob("*.html"):
            html = html_file.read_text(encoding="utf-8")
            html_file.write_text(_rewrite_asset_paths(html, base_url), encoding="utf-8")
    return out
```

**CLI addition in cli.py:**
```python
@cli.command()
@click.option("--base-url", default=None, help="Absolute base URL for CDN/hosted asset paths")
def build(config, metrics, output, open_browser, base_url):
    ...
    builder.build(output_dir=output, base_url=base_url)
```

### Anti-Patterns to Avoid
- **UploadFile in background task:** FastAPI v0.106+ closes the spooled temp file before BackgroundTasks run. Always call `await file.read()` inside the endpoint body and pass raw bytes to the background task.
- **Setting X-Frame-Options: DENY globally:** This blocks all iframe embedding — PLAT-02 requires embedding to work. Only set frame-ancestors on the API routes, not on deck-serving routes.
- **Blocking build in async endpoint:** `PresentationBuilder.build()` is synchronous and CPU-bound. Use `BackgroundTasks` or `asyncio.run_in_executor` to avoid blocking the event loop.
- **Storing analytics in-memory:** Process restarts lose all data. Always flush to SQLite immediately in the `/api/events` endpoint.
- **sendBeacon with beforeunload:** MDN recommends `visibilitychange` instead; `beforeunload` reliability is ~70% across browsers.
- **Single flat StaticFiles mount:** Mounting one directory for all decks means deck isolation is lost. Mount each deck UUID separately under `/d/{deck_id}/`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Rate limiting | Custom request counter middleware | `slowapi` | Handles burst, sliding window, per-IP, in-memory/Redis backends; already battle-tested |
| OpenAPI docs | Manual swagger YAML | FastAPI auto-generates from Pydantic models | No manual sync required; stays consistent with code |
| ASGI static file serving | Custom file send handler | `starlette.StaticFiles` | Handles ETags, content-type, range requests, not-found responses |
| File upload parsing | Manual multipart parser | `python-multipart` via FastAPI `UploadFile` | Handles large files with spooled temp, content-type detection |
| UUID generation | Sequential integer IDs | `uuid.uuid4()` | Unguessable, globally unique, no DB sequence needed |

**Key insight:** The platform layer is intentionally thin — it orchestrates existing `PresentationBuilder` rather than replacing it. All heavy HTML generation stays in `pf/builder.py`.

---

## Common Pitfalls

### Pitfall 1: UploadFile Closed Before Background Task Runs
**What goes wrong:** FastAPI closes `UploadFile`'s spooled temp file after the response is sent. Background tasks run after that point, so `await file.read()` in a background task raises `ValueError: I/O operation on closed file`.
**Why it happens:** FastAPI v0.106.0 changed UploadFile lifecycle — introduced in issue #10936.
**How to avoid:** Read file contents inside the endpoint body before `return`. Pass `bytes`, not the `UploadFile` object, to background tasks.
**Warning signs:** `ValueError: I/O operation on closed file` in background task logs.

### Pitfall 2: WebSocket In-Memory State Lost on Restart
**What goes wrong:** `ConnectionManager.state` (current slide per room) lives in memory. Server restart (or second uvicorn worker) has no state, so new joiners get slide 1 regardless.
**Why it happens:** No persistence layer for WebSocket room state.
**How to avoid:** For v1 (single-process), this is acceptable. Document that presenter sync requires a single uvicorn worker (`--workers 1`). For multi-process: persist room state to SQLite or Redis before broadcasting.
**Warning signs:** Viewers see slide 1 after server restart mid-presentation.

### Pitfall 3: StaticFiles Mount Order vs API Routes
**What goes wrong:** If `StaticFiles` is mounted at `/d/` before API routes are registered, FastAPI may route `/d/something` to static handler instead of a matching API route.
**Why it happens:** FastAPI route matching is first-match; `mount()` creates a catch-all for all sub-paths.
**How to avoid:** Register all API routes (`/api/*`) first, then call `app.mount()` for static directories.
**Warning signs:** 404 or file-not-found on API routes that start with `/d/`.

### Pitfall 4: CORS Not Configured for Embedding
**What goes wrong:** Notion, blog sites, and other embedders are cross-origin. Without CORS headers, the iframe's `fetch()` calls (analytics beacon) are blocked by the browser. Also, `X-Frame-Options: DENY` prevents the iframe from loading at all.
**Why it happens:** FastAPI's default configuration sends no CORS or framing headers.
**How to avoid:** Add `CORSMiddleware` with `allow_origins=["*"]` for public decks. Set `frame-ancestors *` CSP on deck responses. Do not set `X-Frame-Options`.
**Warning signs:** Browser console shows `Refused to display ... in a frame because it set 'X-Frame-Options' to 'deny'`.

### Pitfall 5: sendBeacon Payload > 64KB
**What goes wrong:** Browsers silently drop beacons larger than ~64KB.
**Why it happens:** Beacon API has a size limit; payloads with large content strings exceed it.
**How to avoid:** Keep event payloads minimal: `{deck_id, slide, duration_ms}` only. No slide content in the beacon.
**Warning signs:** Analytics events missing for some slides, no network error visible.

### Pitfall 6: base_url Rewrite Matching CDN-Hosted Font URLs
**What goes wrong:** The regex-based rewriter accidentally rewrites absolute CDN URLs (Google Fonts, jsDelivr) to `base_url + original_url`.
**Why it happens:** Greedy regex matches `href="https://..."` if not properly anchored.
**How to avoid:** Negative lookahead in regex: skip paths that already start with `http`, `https`, `data:`, `//`, or `#`. Test against actual base.html.j2 output with CDN links present.
**Warning signs:** Broken font/CDN URLs in production build output.

---

## Code Examples

Verified patterns from official sources:

### FastAPI App Structure with CORS + Rate Limiter
```python
# Source: FastAPI official docs + slowapi docs
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Presentation Platform API", version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS must be added before other middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # Public platform — all origins
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Pydantic Response Models for OpenAPI
```python
# Source: https://fastapi.tiangolo.com/tutorial/response-model/
from pydantic import BaseModel

class BuildResponse(BaseModel):
    deck_id: str
    url: str
    slide_count: int
    warnings: list[dict] = []

class DashboardEntry(BaseModel):
    slide: int
    views: int
    total_ms: int
    avg_ms: float

@app.post("/api/build", response_model=BuildResponse)
@limiter.limit("10/minute")
async def build_deck(request: Request, config: UploadFile, metrics: UploadFile):
    ...
```

### WebSocket Test Pattern
```python
# Source: https://www.starlette.io/testclient/
from starlette.testclient import TestClient

def test_websocket_sync():
    with TestClient(app) as client:
        with client.websocket_connect("/ws/test-deck-id") as ws:
            ws.send_json({"slide": 3})
            data = ws.receive_json()
            assert data["slide"] == 3
            assert data["type"] == "goto"
```

### Async HTTP Test Pattern (for API routes)
```python
# Source: https://fastapi.tiangolo.com/tutorial/testing/
import pytest
from httpx import AsyncClient, ASGITransport

@pytest.mark.asyncio
async def test_build_endpoint(tmp_path):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        config_bytes = b"meta:\n  title: Test\ntheme:\n  primary: '#1C2537'\n  accent: '#C4A962'\nslides: []"
        metrics_bytes = b"{}"
        response = await ac.post(
            "/api/build",
            files={"config": ("presentation.yaml", config_bytes), "metrics": ("metrics.json", metrics_bytes)},
        )
    assert response.status_code == 200
    assert "deck_id" in response.json()
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `beforeunload` for analytics | `visibilitychange` + `sendBeacon` | MDN recommendation (2022+) | ~30% more reliable beacon delivery |
| `Flask-Limiter` | `slowapi` for Starlette/FastAPI | 2021+ | Native async support, same decorator API |
| Manual OpenAPI YAML | FastAPI auto-generates from Pydantic | FastAPI v0.50+ | No manual schema sync; Swagger UI free |
| `X-Frame-Options` | `Content-Security-Policy: frame-ancestors` | CSP Level 2 (2016), now universal | More granular control over who can embed |
| Requests + TestClient | `httpx.AsyncClient(transport=ASGITransport(...))` | FastAPI 0.92+ | Supports async test client for async routes |

**Deprecated/outdated:**
- `requests.TestClient` for async FastAPI routes: replaced by `httpx.AsyncClient` with `ASGITransport`
- `UploadFile` object passed to `BackgroundTasks`: broken since FastAPI v0.106.0 — pass bytes instead

---

## Open Questions

1. **Job status polling for async builds**
   - What we know: `BackgroundTasks` has no built-in status API; the endpoint returns 200 before build completes.
   - What's unclear: Should `POST /api/build` be synchronous (block until done) or async (return job ID)?
   - Recommendation: For v1, run build synchronously in the endpoint using `asyncio.run_in_executor` to avoid blocking the event loop. Return the result directly. Avoid job status polling complexity.

2. **Deck storage lifecycle / cleanup**
   - What we know: Each deck is a UUID-keyed directory; no TTL or quota logic planned.
   - What's unclear: What happens when disk fills up? How do users delete decks?
   - Recommendation: Add `DELETE /api/decks/{deck_id}` endpoint from the start. Document that v1 has no automatic cleanup.

3. **WebSocket auth for presenter role**
   - What we know: Any client connecting to `/ws/{deck_id}` can broadcast position changes (last-writer-wins).
   - What's unclear: Should only the "presenter" role be able to change slide position, or can all viewers change it?
   - Recommendation: For v1, implement PLAT-04 as stated (any connected client can change position). Role-based presenter auth is a v2 concern. Document the behavior clearly.

4. **Multi-file StaticFiles mount scalability**
   - What we know: Each deck UUID requires a separate `app.mount()` call.
   - What's unclear: FastAPI/Starlette's behavior when 1,000+ mounts are registered.
   - Recommendation: For v1 (few decks), separate mounts are fine. If scale becomes an issue, replace with a custom route that reads files from disk. Flag this as a known limitation.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (existing) |
| Config file | None (uses pytest auto-discovery) |
| Quick run command | `pytest tests/test_platform_api.py tests/test_platform_analytics.py tests/test_platform_sync.py -x` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PLAT-06 | `_rewrite_asset_paths()` turns relative hrefs absolute | unit | `pytest tests/test_platform_api.py::test_base_url_rewrite -x` | Wave 0 |
| PLAT-06 | `pf build --base-url` passes through to builder | unit | `pytest tests/test_cli.py::test_build_base_url -x` | Wave 0 |
| PLAT-01 | `POST /api/build` returns `deck_id` + `url` | integration | `pytest tests/test_platform_api.py::test_build_endpoint -x` | Wave 0 |
| PLAT-01 | Uploaded deck is served at `/d/{deck_id}/present.html` | integration | `pytest tests/test_platform_api.py::test_deck_served -x` | Wave 0 |
| PLAT-02 | `/d/{deck_id}/` response has `frame-ancestors *` CSP header | integration | `pytest tests/test_platform_api.py::test_embed_headers -x` | Wave 0 |
| PLAT-05 | `POST /api/validate` returns validation errors list | integration | `pytest tests/test_platform_api.py::test_validate_endpoint -x` | Wave 0 |
| PLAT-05 | Rate limit exceeded returns 429 | integration | `pytest tests/test_platform_api.py::test_rate_limit -x` | Wave 0 |
| PLAT-03 | `POST /api/events` records event to SQLite | unit | `pytest tests/test_platform_analytics.py::test_record_event -x` | Wave 0 |
| PLAT-03 | `GET /api/decks/{deck_id}/dashboard` returns per-slide stats | integration | `pytest tests/test_platform_analytics.py::test_dashboard -x` | Wave 0 |
| PLAT-04 | WebSocket `/ws/{deck_id}` broadcasts slide position | integration | `pytest tests/test_platform_sync.py::test_broadcast -x` | Wave 0 |
| PLAT-04 | New joiner receives current slide on connect | integration | `pytest tests/test_platform_sync.py::test_new_joiner_sync -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_platform_api.py tests/test_platform_analytics.py tests/test_platform_sync.py -x`
- **Per wave merge:** `pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_platform_api.py` — covers PLAT-01, PLAT-02, PLAT-05, PLAT-06 (CLI)
- [ ] `tests/test_platform_analytics.py` — covers PLAT-03
- [ ] `tests/test_platform_sync.py` — covers PLAT-04
- [ ] `platform/__init__.py` — package stub
- [ ] `platform/api.py` — FastAPI app stub
- [ ] Framework install: `pip install httpx pytest-asyncio` — needed for async test client

---

## Sources

### Primary (HIGH confidence)
- [FastAPI official docs — WebSockets](https://fastapi.tiangolo.com/advanced/websockets/) — connection manager pattern, broadcast, WebSocketDisconnect
- [FastAPI official docs — Request Files](https://fastapi.tiangolo.com/tutorial/request-files/) — UploadFile attributes, multiple files, async methods
- [FastAPI official docs — Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/) — lifecycle, UploadFile-closed-before-BG-task behavior
- [FastAPI official docs — Static Files](https://fastapi.tiangolo.com/tutorial/static-files/) — StaticFiles mount, html=True
- [MDN — navigator.sendBeacon()](https://developer.mozilla.org/en-US/docs/Web/API/Navigator/sendBeacon) — recommended event (`visibilitychange`), payload size limits
- [MDN — CSP: frame-ancestors](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Security-Policy/frame-ancestors) — iframe embedding headers
- [slowapi docs](https://slowapi.readthedocs.io/) — FastAPI rate limiting decorator syntax, `request` parameter requirement

### Secondary (MEDIUM confidence)
- [WebSocket/SSE blog (2025)](https://blog.greeden.me/en/2025/10/28/weaponizing-real-time-websocket-sse-notifications-with-fastapi-connection-management-rooms-reconnection-scale-out-and-observability/) — room-based ConnectionManager pattern with `rooms: Dict[str, Set[WebSocket]]`
- [FastAPI GitHub discussion #10936](https://github.com/fastapi/fastapi/discussions/10936) — UploadFile closed before BackgroundTasks confirmed bug/limitation
- [slowapi GitHub](https://github.com/laurentS/slowapi) — version info, limitations (no WebSocket support)

### Tertiary (LOW confidence)
- Various WebSearch results for analytics beacon patterns — confirmed against MDN primary source

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — FastAPI, uvicorn, python-multipart, slowapi all verified via official docs and PyPI
- Architecture: HIGH — all six patterns derived from official FastAPI docs or verified secondary sources
- Pitfalls: HIGH — UploadFile background task issue confirmed in FastAPI GitHub discussions; others derived from official CSP and beacon API docs
- Validation architecture: HIGH — matches existing pytest + tmp_path pattern in the codebase

**Research date:** 2026-03-07
**Valid until:** 2026-06-07 (stable libraries; FastAPI WebSocket API is stable, slowapi patterns are stable)
