---
phase: 04-hosted-platform
plan: 02
subsystem: platform
tags: [fastapi, rest-api, rate-limiting, cors, csp, iframe-embedding, uvicorn, cli]

requires:
  - phase: 04-hosted-platform
    plan: 01
    provides: "base_url parameter on PresentationBuilder.build() for hosted deck asset paths"

provides:
  - "pf_platform package (api.py, storage.py, worker.py) — FastAPI REST platform"
  - "POST /api/build — uploads config+metrics, builds deck, returns shareable URL"
  - "POST /api/validate — validates presentation YAML, returns structured errors"
  - "GET /api/decks/{deck_id}/embed — returns iframe HTML snippet"
  - "DELETE /api/decks/{deck_id} — removes built deck"
  - "GET /d/{deck_id}/present.html — serves built deck with CSP frame-ancestors * header"
  - "pf platform serve CLI command — starts uvicorn FastAPI server"

affects: [04-03, 04-04]

tech-stack:
  added:
    - "fastapi>=0.110 — REST framework with OpenAPI docs"
    - "uvicorn>=0.27 — ASGI server for FastAPI"
    - "python-multipart>=0.0.9 — UploadFile support in FastAPI"
    - "slowapi>=0.1.9 — Rate limiting middleware for FastAPI (limits library)"
  patterns:
    - "UUID-keyed deck directories: each build gets store_dir/deck_id/ with presentation.yaml + metrics.json + slides/"
    - "Lazy StaticFiles mounting: app.mount() called after build, not at startup — avoids route capture issues"
    - "EmbedHeadersMiddleware: BaseHTTPMiddleware subclass that adds CSP frame-ancestors on /d/* responses"
    - "Run sync build in executor: asyncio.get_event_loop().run_in_executor(None, functools.partial(run_build, ...))"
    - "pf_platform name (not platform) — avoids shadowing Python stdlib platform module"

key-files:
  created:
    - "pf_platform/__init__.py"
    - "pf_platform/storage.py"
    - "pf_platform/worker.py"
    - "pf_platform/api.py"
    - "tests/test_platform_api.py"
  modified:
    - "pf/cli.py"
    - "setup.py"

key-decisions:
  - "Renamed package from platform/ to pf_platform/ — stdlib collision: Python's own platform module is used by attrs/jsonschema; shadowing it breaks imports"
  - "Lazy StaticFiles mounting per deck via _mount_deck() helper — routes registered first to avoid first-match capture of /d/ swallowing /api/ calls"
  - "load_config() must be called before validate_config() — config stored as instance attribute, not auto-loaded in __init__"
  - "slowapi.storage.reset() in rate limit test — clears request counter between test runs to get a clean 10/min window"

patterns-established:
  - "Platform worker pattern: run_build(deck_dir, base_url) wraps PresentationBuilder synchronously, returns result dict with slide_count/warnings/error"
  - "Storage abstraction: STORE_DIR module constant overridable via monkeypatch — clean test isolation without temp file plumbing"

requirements-completed: [PLAT-01, PLAT-02, PLAT-05]

duration: 10min
completed: 2026-03-07
---

# Phase 4 Plan 02: FastAPI Platform Service Summary

**FastAPI platform API with UUID-keyed deck storage, synchronous build worker, CORS/rate-limiting/CSP middleware, iframe embed support, and `pf platform serve` CLI command — full hosted deck sharing pipeline in 466 passing tests**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-03-07T15:15:12Z
- **Completed:** 2026-03-07T15:25:53Z
- **Tasks:** 3 completed
- **Files modified/created:** 7

## Accomplishments

- `pf_platform/storage.py` — UUID-keyed directory management: `store_deck()`, `get_deck_dir()`, `delete_deck()`, `get_slides_dir()` with overridable `STORE_DIR` constant for test isolation
- `pf_platform/worker.py` — `run_build(deck_dir, base_url)` wraps `PresentationBuilder` synchronously, returns `{slide_count, warnings, contrast_warnings}` or `{error}` on failure
- `pf_platform/api.py` — FastAPI app with CORS (all origins), slowapi rate limiting, `EmbedHeadersMiddleware` (CSP `frame-ancestors *` on `/d/*`), and 4 endpoints: `POST /api/build`, `POST /api/validate`, `GET /api/decks/{id}/embed`, `DELETE /api/decks/{id}`
- `pf/cli.py` — `pf platform serve` command (uvicorn runner with `--host`, `--port`, `--reload`; lazy import with helpful install message)
- `setup.py` — `platform` and `dev` extras_require groups added
- `tests/test_platform_api.py` — 9 integration tests covering all endpoints + rate limiting; all pass

## Task Commits

Each task was committed atomically:

1. **Task 1: Create pf_platform package with storage, worker, and FastAPI app** — `a9f906a` (feat)
2. **Task 2: Add pf platform serve CLI command** — `41f4fa9` (feat)
3. **Task 3: Integration tests for platform API endpoints** — `e6d0d52` (feat)

**Plan metadata:** (final docs commit below)

## Files Created/Modified

- `pf_platform/__init__.py` — Package marker
- `pf_platform/storage.py` — UUID deck directory management
- `pf_platform/worker.py` — Synchronous build job wrapper
- `pf_platform/api.py` — FastAPI app with all endpoints and middleware
- `pf/cli.py` — Added `platform` group + `serve` command
- `setup.py` — Added `platform` and `dev` extras_require
- `tests/test_platform_api.py` — 9 integration tests

## Decisions Made

- **`pf_platform` not `platform`:** Python's built-in `platform` stdlib module is imported by `attrs` (via `_compat.py`) which is used by `jsonschema`. Naming our package `platform/` causes an `AttributeError: module 'platform' has no attribute 'python_implementation'` when any transitive dependency tries to use the stdlib. Renaming to `pf_platform` eliminates the collision.

- **Lazy StaticFiles mounting:** Routes are registered at import time, but `StaticFiles` mounts are added dynamically after each build completes. This avoids the FastAPI first-match routing issue where a mounted `/d/` StaticFiles would capture all routes starting with `/d/`, including hypothetical future API routes.

- **`load_config()` before `validate_config()`:** `PresentationBuilder.__init__` does not auto-load config. The `validate_config()` method reads `self.config` which defaults to `{}`. The `/api/validate` endpoint must call `builder.load_config()` first.

- **`limiter._storage.reset()` in rate limit test:** The slowapi rate limiter uses shared in-memory storage. Resetting between test runs ensures the 10/minute window is fresh for each rate limit test.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Renamed `platform/` to `pf_platform/` to resolve stdlib collision**
- **Found during:** Task 1 verification
- **Issue:** Python's `attrs` library imports the stdlib `platform` module at startup. Our `platform/` directory shadowed it, causing `AttributeError: module 'platform' has no attribute 'python_implementation'` when `jsonschema` (and thus `PresentationBuilder`) was imported.
- **Fix:** Renamed directory `platform/` → `pf_platform/`, updated all internal imports from `platform.*` to `pf_platform.*`, updated `pf/cli.py` uvicorn import string to `pf_platform.api:app`
- **Files modified:** `pf_platform/__init__.py`, `pf_platform/api.py`, `pf/cli.py`
- **Commit:** a9f906a (included in Task 1 commit)

**2. [Rule 1 - Bug] Added `load_config()` call before `validate_config()` in validate endpoint**
- **Found during:** Task 3 test writing
- **Issue:** `PresentationBuilder.validate_config()` uses `self.config` which is only populated after `load_config()` is called. The endpoint was calling `validate_config()` on an empty config, always returning no errors.
- **Fix:** Added `builder.load_config()` call before `builder.validate_config()` in the validate endpoint
- **Files modified:** `pf_platform/api.py`
- **Commit:** e6d0d52 (included in Task 3 commit)

## Issues Encountered

None beyond the deviations above.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- FastAPI platform service is fully operational; 04-03 and 04-04 can build on the `/api/build` endpoint and deck serving infrastructure
- All 466 tests pass (9 new + 457 existing)
- `pf platform serve` starts the server; `pip install presentation-framework[platform]` installs deps

---
*Phase: 04-hosted-platform*
*Completed: 2026-03-07*

## Self-Check: PASSED

- pf_platform/__init__.py: FOUND
- pf_platform/api.py: FOUND, contains FastAPI app with rate limiting and CORS
- pf_platform/storage.py: FOUND, contains store_deck
- pf_platform/worker.py: FOUND, contains run_build
- tests/test_platform_api.py: FOUND, contains test_build_endpoint
- pf/cli.py: FOUND, contains platform serve command
- setup.py: FOUND, contains platform extras
- Commit a9f906a: FOUND
- Commit 41f4fa9: FOUND
- Commit e6d0d52: FOUND
