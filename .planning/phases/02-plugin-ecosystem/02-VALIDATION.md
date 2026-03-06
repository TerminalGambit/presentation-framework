---
phase: 2
slug: plugin-ecosystem
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-06
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (already installed) |
| **Config file** | None — uses default discovery |
| **Quick run command** | `pytest tests/test_registry.py -x` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_registry.py -x`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | PLUG-01 | unit | `pytest tests/test_registry.py::test_layout_discovery_via_entry_points -x` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 1 | PLUG-01 | unit | `pytest tests/test_registry.py::test_local_directory_discovery -x` | ❌ W0 | ⬜ pending |
| 02-01-03 | 01 | 1 | PLUG-01 | unit | `pytest tests/test_registry.py::test_builder_uses_choice_loader -x` | ❌ W0 | ⬜ pending |
| 02-02-01 | 02 | 1 | PLUG-05 | unit | `pytest tests/test_registry.py::test_template_inheritance -x` | ❌ W0 | ⬜ pending |
| 02-02-02 | 02 | 1 | PLUG-06 | unit | `pytest tests/test_registry.py::test_css_injection -x` | ❌ W0 | ⬜ pending |
| 02-02-03 | 02 | 1 | PLUG-06 | integration | `pytest tests/test_registry.py::test_css_isolation -x` | ❌ W0 | ⬜ pending |
| 02-03-01 | 03 | 2 | PLUG-02 | unit | `pytest tests/test_registry.py::test_theme_discovery -x` | ❌ W0 | ⬜ pending |
| 02-03-02 | 03 | 2 | PLUG-02 | unit | `pytest tests/test_builder.py::test_theme_plugin_merge -x` | ❌ W0 | ⬜ pending |
| 02-04-01 | 04 | 2 | PLUG-03 | unit | `pytest tests/test_datasources.py::test_datasource_fetch_merges_metrics -x` | ❌ W0 | ⬜ pending |
| 02-04-02 | 04 | 2 | PLUG-03 | unit | `pytest tests/test_datasources.py::test_missing_credentials_raises -x` | ❌ W0 | ⬜ pending |
| 02-05-01 | 05 | 3 | PLUG-04 | unit | `pytest tests/test_cli.py::test_plugins_list -x` | ❌ W0 | ⬜ pending |
| 02-05-02 | 05 | 3 | PLUG-04 | unit | `pytest tests/test_cli.py::test_plugins_install -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_registry.py` — stubs for PLUG-01, PLUG-05, PLUG-06
- [ ] `tests/test_datasources.py` — stubs for PLUG-03
- [ ] `tests/test_cli.py` — extend for PLUG-04 plugin CLI commands
- [ ] `pf/registry.py` — core registry module (does not exist yet)

*No framework install needed — pytest already present*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Plugin CSS visually isolated | PLUG-06 | Visual inspection of rendered slides | Build deck with core + plugin layouts, verify plugin styles don't bleed |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
