---
phase: 3
slug: llm-integration
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-06
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x+ |
| **Config file** | none — default discovery |
| **Quick run command** | `python3 -m pytest tests/test_llm_schemas.py tests/test_optimizer.py tests/test_accessibility.py -x -q` |
| **Full suite command** | `python3 -m pytest tests/ -v` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python3 -m pytest tests/test_llm_schemas.py tests/test_optimizer.py tests/test_accessibility.py tests/test_mcp_server.py -x -q`
- **After every plan wave:** Run `python3 -m pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | LLM-01 | unit | `python3 -m pytest tests/test_llm_schemas.py::test_timeline_schema_has_maxitems -x` | ❌ W0 | ⬜ pending |
| 03-01-02 | 01 | 1 | LLM-01 | unit | `python3 -m pytest tests/test_llm_schemas.py::test_all_schemas_have_constraints -x` | ❌ W0 | ⬜ pending |
| 03-02-01 | 02 | 1 | LLM-05 | unit | `python3 -m pytest tests/test_optimizer.py::test_split_two_column -x` | ❌ W0 | ⬜ pending |
| 03-02-02 | 02 | 1 | LLM-05 | unit | `python3 -m pytest tests/test_optimizer.py::test_split_single_overflow_no_empty -x` | ❌ W0 | ⬜ pending |
| 03-03-01 | 03 | 2 | LLM-02 | integration | `python3 -m pytest tests/test_mcp_server.py::TestGeneratePresentation -x` | ❌ W0 | ⬜ pending |
| 03-03-02 | 03 | 2 | LLM-02 | unit | `python3 -m pytest tests/test_mcp_server.py::test_generate_requires_llm_extra -x` | ❌ W0 | ⬜ pending |
| 03-03-03 | 03 | 2 | LLM-07 | unit | `python3 -m pytest tests/test_builder.py::test_llm_content_escaping -x` | ❌ W0 | ⬜ pending |
| 03-03-04 | 03 | 2 | LLM-07 | unit | `python3 -m pytest tests/test_builder.py::test_safe_llm_text_strips_script -x` | ❌ W0 | ⬜ pending |
| 03-04-01 | 04 | 3 | LLM-03 | integration | `python3 -m pytest tests/test_mcp_server.py::TestSuggestLayout -x` | ❌ W0 | ⬜ pending |
| 03-04-02 | 04 | 3 | LLM-04 | smoke | `python3 -m pytest tests/test_multiagent_workflow.py -x` | ❌ W0 | ⬜ pending |
| 03-04-03 | 04 | 3 | LLM-05 | unit | `python3 -m pytest tests/test_mcp_server.py::TestOptimizeSlide -x` | ❌ W0 | ⬜ pending |
| 03-05-01 | 05 | 1 | LLM-06 | unit | `python3 -m pytest tests/test_accessibility.py::test_warns_missing_alt -x` | ❌ W0 | ⬜ pending |
| 03-05-02 | 05 | 1 | LLM-06 | unit | `python3 -m pytest tests/test_accessibility.py::test_warns_missing_aria -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_llm_schemas.py` — stubs for LLM-01 (per-layout schema constraints)
- [ ] `tests/test_optimizer.py` — stubs for LLM-05 (split_slide algorithm, edge cases)
- [ ] `tests/test_accessibility.py` — stubs for LLM-06 (ARIA label scan, alt text warnings)
- [ ] `tests/test_multiagent_workflow.py` — stubs for LLM-04 (sequential MCP tool calls)

*Additions to `tests/test_mcp_server.py` for LLM-02, LLM-03, LLM-05 MCP surface are in-file additions, not new files*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Visual slide rendering after split | LLM-05 | Requires visual inspection of split layout fidelity | Build a 12-card two-column slide, run optimizer, open both resulting slides in browser |
| Screen reader navigation | LLM-06 | Requires assistive technology | Open built deck in VoiceOver, tab through interactive elements |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
