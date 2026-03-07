---
phase: 04-hosted-platform
plan: "03"
subsystem: analytics
tags: [sqlite, fastapi, analytics, beacon, dashboard]

requires:
  - phase: 04-02
    provides: FastAPI app with build/validate/embed/delete endpoints and WebSocket sync

provides:
  - pf_platform/analytics.py — SQLite event store (init_db, record_event, get_dashboard, get_total_views)
  - BEACON_SCRIPT constant — JS client-side slide tracking pattern
  - POST /api/events — beacon ingestion endpoint
  - GET /api/decks/{deck_id}/dashboard — per-slide aggregated analytics
  - GET /api/beacon-script?deck_id=X — script endpoint with context injected
  - tests/test_platform_analytics.py — 10 tests (7 unit + 3 integration)

affects:
  - future deck-serving that injects beacon into present.html
  - platform operator dashboards and reporting UIs

tech-stack:
  added: [sqlite3 (stdlib)]
  patterns:
    - db_path override pattern for testable SQLite modules
    - asynccontextmanager lifespan for FastAPI startup hooks (replaces deprecated on_event)
    - navigator.sendBeacon for fire-and-forget analytics pings

key-files:
  created:
    - pf_platform/analytics.py
    - tests/test_platform_analytics.py
  modified:
    - pf_platform/api.py

key-decisions:
  - "Analytics beacon uses navigator.sendBeacon (fire-and-forget) — tolerates page close without blocking navigation"
  - "DB_PATH module-level with db_path parameter override — same testability pattern as STORE_DIR in storage.py"
  - "No rate limiting on POST /api/events — beacons are high-frequency by design; rate limiting would drop legitimate events"
  - "asynccontextmanager lifespan replaces deprecated @app.on_event('startup') to avoid FastAPI deprecation warnings"
  - "BEACON_SCRIPT exposed via GET /api/beacon-script endpoint so deck-serving can inject correct __PF_ANALYTICS_URL and __PF_DECK_ID vars"

patterns-established:
  - "SQLite init_db() idempotent (CREATE TABLE IF NOT EXISTS) so record_event() can call it safely on every write"
  - "Integration tests monkeypatch both analytics.DB_PATH and storage.STORE_DIR to tmp_path for full isolation"

requirements-completed: [PLAT-03]

duration: 5min
completed: "2026-03-07"
---

# Phase 4 Plan 3: Analytics Tracking Summary

**SQLite-backed slide view analytics with per-deck dashboard API, JS beacon client pattern, and 10-test suite covering store correctness and API integration**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-07T15:28:25Z
- **Completed:** 2026-03-07T15:34:07Z
- **Tasks:** 2/2
- **Files modified:** 3

## Accomplishments

- Created `pf_platform/analytics.py` with idempotent `init_db()`, `record_event()`, `get_dashboard()`, and `get_total_views()` backed by SQLite
- Added `BEACON_SCRIPT` constant providing the JS pattern for client-side slide tracking via `navigator.sendBeacon`
- Registered `POST /api/events`, `GET /api/decks/{deck_id}/dashboard`, and `GET /api/beacon-script` endpoints in `pf_platform/api.py`
- Created 10-test suite: 7 unit tests for the SQLite store + 3 integration tests for the API endpoints (all pass)

## Task Commits

1. **Task 1: Analytics SQLite store and wire API endpoints** - `6e05742` (feat)
2. **Task 2: Tests for analytics store and API endpoints** - `7de5946` (test)

**Plan metadata:** (this commit)

## Files Created/Modified

- `pf_platform/analytics.py` — SQLite event store with init_db, record_event, get_dashboard, get_total_views; BEACON_SCRIPT JS constant
- `pf_platform/api.py` — Added analytics imports, Pydantic models (EventPayload, DashboardEntry, DashboardResponse), three new endpoints, asynccontextmanager lifespan for DB init
- `tests/test_platform_analytics.py` — 10 tests covering all store functions and API endpoints

## Decisions Made

- **No rate limiting on /api/events**: Beacon calls are fire-and-forget and high-frequency; adding rate limits would silently drop legitimate view data. Documented explicitly in code and plan.
- **DB_PATH override pattern**: Matches `storage.STORE_DIR` convention established in plan 04-02 — `db_path: Path | None = None` parameter on all functions, defaulting to module-level `DB_PATH`. Makes unit testing fully isolated without monkeypatching the filesystem.
- **asynccontextmanager lifespan**: The deprecated `@app.on_event("startup")` caused DeprecationWarning in tests. Converted to `asynccontextmanager` lifespan pattern (the recommended FastAPI approach) during Task 2 implementation.
- **beacon-script endpoint**: Rather than hardcoding the analytics URL in the script, `GET /api/beacon-script?deck_id=X` returns a script fragment that sets `window.__PF_ANALYTICS_URL` and `window.__PF_DECK_ID` — making the endpoint context-aware and usable as a `<script src=...>` tag.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Updated editable install to include pf_platform in MAPPING**
- **Found during:** Task 2 (test execution)
- **Issue:** The pip editable install only mapped the `pf` package; `pf_platform` was missing from the finder MAPPING, causing `ModuleNotFoundError` in pytest
- **Fix:** Ran `pip install -e .` to regenerate the editable finder with both `pf` and `pf_platform` in the MAPPING
- **Files modified:** `/Users/jackmassey/Library/Python/3.13/lib/python/site-packages/__editable___presentation_framework_0_2_0_finder.py` (auto-generated)
- **Verification:** All 10 tests pass under system Python 3.13
- **Committed in:** 7de5946 (Task 2 commit)

**2. [Rule 1 - Bug] Replaced deprecated @app.on_event with asynccontextmanager lifespan**
- **Found during:** Task 2 (test run showed DeprecationWarning)
- **Issue:** `@app.on_event("startup")` is deprecated in FastAPI; generated warnings in test output
- **Fix:** Added `contextlib.asynccontextmanager` import, replaced decorator with `_lifespan` context manager passed to `FastAPI(lifespan=_lifespan)`
- **Files modified:** `pf_platform/api.py`
- **Verification:** All 10 analytics tests + all 9 existing platform API tests pass cleanly, no warnings
- **Committed in:** 7de5946 (Task 2 commit)

**3. [Rule 2 - Missing Critical] Added importorskip("slowapi") to test module**
- **Found during:** Task 2 (integration test setup error)
- **Issue:** Plan's fixture imports `pf_platform.api` which imports `slowapi`; without `importorskip`, tests error rather than skip in envs without platform deps (inconsistent with existing test_platform_api.py pattern)
- **Fix:** Added `pytest.importorskip("slowapi")` at module top
- **Files modified:** `tests/test_platform_analytics.py`
- **Verification:** Module skips gracefully in miniconda env; all 10 tests run correctly in system Python env
- **Committed in:** 7de5946 (Task 2 commit)

---

**Total deviations:** 3 auto-fixed (1 Rule 3 blocking, 1 Rule 1 bug, 1 Rule 2 missing critical)
**Impact on plan:** All auto-fixes necessary for correctness and test environment compatibility. No scope creep.

## Issues Encountered

None beyond the auto-fixed deviations above.

## User Setup Required

None — analytics data is stored in `data/analytics.db` alongside the deck files. No external services or environment variables required.

## Next Phase Readiness

- Analytics store complete; ready for deck-serving to inject beacon script into `present.html`
- `GET /api/beacon-script?deck_id=X` endpoint available for future automatic script injection
- Dashboard data available for operator/author UI development

---
*Phase: 04-hosted-platform*
*Completed: 2026-03-07*
