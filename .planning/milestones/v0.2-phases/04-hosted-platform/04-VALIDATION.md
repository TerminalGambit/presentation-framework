---
phase: 4
slug: hosted-platform
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-07
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (existing) + pytest-asyncio |
| **Config file** | None (uses pytest auto-discovery) |
| **Quick run command** | `pytest tests/test_platform_api.py tests/test_platform_analytics.py tests/test_platform_sync.py -x` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_platform_api.py tests/test_platform_analytics.py tests/test_platform_sync.py -x`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | PLAT-06 | unit | `pytest tests/test_platform_api.py::test_base_url_rewrite -x` | ❌ W0 | ⬜ pending |
| 04-01-02 | 01 | 1 | PLAT-06 | unit | `pytest tests/test_cli.py::test_build_base_url -x` | ❌ W0 | ⬜ pending |
| 04-02-01 | 02 | 2 | PLAT-01 | integration | `pytest tests/test_platform_api.py::test_build_endpoint -x` | ❌ W0 | ⬜ pending |
| 04-02-02 | 02 | 2 | PLAT-01 | integration | `pytest tests/test_platform_api.py::test_deck_served -x` | ❌ W0 | ⬜ pending |
| 04-03-01 | 03 | 2 | PLAT-02 | integration | `pytest tests/test_platform_api.py::test_embed_headers -x` | ❌ W0 | ⬜ pending |
| 04-04-01 | 04 | 3 | PLAT-05 | integration | `pytest tests/test_platform_api.py::test_validate_endpoint -x` | ❌ W0 | ⬜ pending |
| 04-04-02 | 04 | 3 | PLAT-05 | integration | `pytest tests/test_platform_api.py::test_rate_limit -x` | ❌ W0 | ⬜ pending |
| 04-05-01 | 05 | 3 | PLAT-03 | unit | `pytest tests/test_platform_analytics.py::test_record_event -x` | ❌ W0 | ⬜ pending |
| 04-05-02 | 05 | 3 | PLAT-03 | integration | `pytest tests/test_platform_analytics.py::test_dashboard -x` | ❌ W0 | ⬜ pending |
| 04-06-01 | 06 | 4 | PLAT-04 | integration | `pytest tests/test_platform_sync.py::test_broadcast -x` | ❌ W0 | ⬜ pending |
| 04-06-02 | 06 | 4 | PLAT-04 | integration | `pytest tests/test_platform_sync.py::test_new_joiner_sync -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_platform_api.py` — stubs for PLAT-01, PLAT-02, PLAT-05, PLAT-06
- [ ] `tests/test_platform_analytics.py` — stubs for PLAT-03
- [ ] `tests/test_platform_sync.py` — stubs for PLAT-04
- [ ] `pip install httpx pytest-asyncio` — needed for async test client
- [ ] `platform/__init__.py` — package stub
- [ ] `platform/api.py` — FastAPI app stub

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| iframe embeds in Notion/blog | PLAT-02 | Cross-origin embedding needs real browser context | Deploy locally, create iframe snippet, paste into Notion page, verify slide navigation works |
| Analytics beacon fires on tab close | PLAT-03 | `visibilitychange` event unreliable in test runners | Open deck in browser, navigate slides, close tab, verify events in SQLite DB |
| WebSocket sync across multiple browsers | PLAT-04 | Multi-client real-time needs actual browser sessions | Open two browser tabs to same `/ws/{deck_id}`, navigate in one, verify the other follows |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
