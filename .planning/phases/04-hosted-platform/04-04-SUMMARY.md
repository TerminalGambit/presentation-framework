---
phase: 04-hosted-platform
plan: "04"
subsystem: pf_platform
tags:
  - websocket
  - real-time
  - sync
  - presenter
dependency_graph:
  requires:
    - 04-02 (FastAPI app, storage, rate limiting)
  provides:
    - pf_platform/sync.py (ConnectionManager, SYNC_SCRIPT)
    - WebSocket /ws/{deck_id} endpoint
    - Real-time presenter sync broadcast
  affects:
    - pf_platform/api.py (WebSocket endpoint added)
tech_stack:
  added:
    - WebSocket via FastAPI/Starlette
    - ConnectionManager singleton (room-based, last-writer-wins)
  patterns:
    - Room-keyed WebSocket management with dead-connection cleanup
    - Starlette TestClient with shared instance for concurrent WS tests
key_files:
  created:
    - pf_platform/sync.py
    - tests/test_platform_sync.py
  modified:
    - pf_platform/api.py
decisions:
  - "Single TestClient instance required for multi-connection WS tests — separate TestClient instances run separate ASGI transports and cannot share room state"
  - "SYNC_SCRIPT included as module-level constant for JS client wiring pattern documentation"
metrics:
  duration: "3 min"
  completed: "2026-03-07"
  tasks: 2
  files: 3
---

# Phase 04 Plan 04: WebSocket Presenter Sync Summary

**One-liner:** Room-based WebSocket sync with last-writer-wins broadcast using a ConnectionManager singleton and `/ws/{deck_id}` FastAPI endpoint.

## What Was Built

### `pf_platform/sync.py` — ConnectionManager

- `ConnectionManager` class with `rooms: Dict[str, Set[WebSocket]]` and `state: Dict[str, int]`
- `connect()` — accepts WebSocket, adds to room, sends current slide state as `{"slide": N, "type": "sync"}`
- `disconnect()` — removes client from room, deletes empty rooms
- `broadcast()` — sends JSON to all room members, auto-cleans dead connections
- `set_slide()` — updates canonical slide position (last-writer-wins)
- `SYNC_SCRIPT` — JS client wiring pattern for platform-served decks
- Module-level `manager` singleton

### `pf_platform/api.py` — WebSocket Endpoint

Added `@app.websocket("/ws/{deck_id}")` endpoint:
- Connects client to room via `manager.connect()`
- Receives `{"slide": N}` messages in a loop
- Calls `manager.set_slide()` + `manager.broadcast()` for each message
- Handles `WebSocketDisconnect` and general exceptions with `manager.disconnect()` cleanup

### `tests/test_platform_sync.py` — 6 Tests

All 6 tests pass:

| Test | Behavior Verified |
|------|-------------------|
| `test_new_joiner_receives_current_slide` | Default slide=1 for unknown deck |
| `test_joiner_after_state_set` | Initial sync delivers current state |
| `test_broadcast_slide_position` | Slide change broadcasts to all room members |
| `test_disconnect_cleanup` | Disconnected clients removed from room |
| `test_independent_rooms` | Different deck_ids have isolated state |
| `test_last_writer_wins` | Final position wins; manager.state updated correctly |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Two separate TestClient instances cannot share WebSocket room state**

- **Found during:** Task 2 (test_broadcast_slide_position)
- **Issue:** Each `TestClient` instance creates a separate ASGI transport with its own event loop thread. Two separate instances cannot have concurrent WebSocket connections share the same in-process manager singleton because the WS state is partitioned across transports.
- **Fix:** Refactored to use a single `client` fixture (shared `TestClient` instance) across all tests. Concurrent connections use `threading.Thread` within the same client context, which correctly shares the ASGI event loop.
- **Files modified:** `tests/test_platform_sync.py`
- **Commit:** 8353d61

## Self-Check: PASSED

Files created/modified:
- FOUND: pf_platform/sync.py
- FOUND: tests/test_platform_sync.py
- FOUND: pf_platform/api.py (WebSocket endpoint added)

Commits verified:
- 499a008 feat(04-04): add ConnectionManager and WebSocket /ws/{deck_id} endpoint
- 8353d61 test(04-04): add WebSocket sync tests for ConnectionManager
