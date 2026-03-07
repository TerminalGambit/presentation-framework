---
phase: 1
slug: rich-media-export-polish
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-06
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (existing, version in project deps) |
| **Config file** | None detected — uses pytest defaults |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | MEDIA-01 | unit | `pytest tests/test_code_block.py -x` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 1 | MEDIA-01 | unit | `pytest tests/test_code_block.py::test_no_code_no_cdn -x` | ❌ W0 | ⬜ pending |
| 01-01-03 | 01 | 1 | MEDIA-01 | unit | `pytest tests/test_code_block.py::test_theme_selection -x` | ❌ W0 | ⬜ pending |
| 01-02-01 | 02 | 1 | MEDIA-02 | unit | `pytest tests/test_fragments.py::test_block_fragment_class -x` | ❌ W0 | ⬜ pending |
| 01-02-02 | 02 | 1 | MEDIA-02 | unit | `pytest tests/test_fragments.py::test_bullet_fragment_class -x` | ❌ W0 | ⬜ pending |
| 01-03-01 | 03 | 2 | MEDIA-03 | unit | `pytest tests/test_mermaid.py::test_mermaid_layout_renders -x` | ❌ W0 | ⬜ pending |
| 01-03-02 | 03 | 2 | MEDIA-03 | unit | `pytest tests/test_mermaid.py::test_cdn_auto_detect -x` | ❌ W0 | ⬜ pending |
| 01-04-01 | 04 | 2 | MEDIA-04 | unit | `pytest tests/test_video.py::test_youtube_thumbnail -x` | ❌ W0 | ⬜ pending |
| 01-04-02 | 04 | 2 | MEDIA-04 | unit | `pytest tests/test_video.py::test_mp4_embed -x` | ❌ W0 | ⬜ pending |
| 01-04-03 | 04 | 2 | MEDIA-05 | unit | `pytest tests/test_map.py::test_map_renders_leaflet -x` | ❌ W0 | ⬜ pending |
| 01-04-04 | 04 | 2 | MEDIA-05 | unit | `pytest tests/test_map.py::test_cdn_auto_detect -x` | ❌ W0 | ⬜ pending |
| 01-05-01 | 05 | 2 | MEDIA-06 | unit | `pytest tests/test_custom_style.py::test_style_key_injected -x` | ❌ W0 | ⬜ pending |
| 01-05-02 | 05 | 2 | MEDIA-07 | unit | `pytest tests/test_toc.py::test_toc_collects_sections -x` | ❌ W0 | ⬜ pending |
| 01-06-01 | 06 | 3 | EXPORT-01 | unit | `pytest tests/test_export_sentinel.py::test_sentinel_in_static_slide -x` | ❌ W0 | ⬜ pending |
| 01-06-02 | 06 | 3 | EXPORT-02 | unit | `pytest tests/test_pptx_native.py::TestTitleLayout -x` | ❌ W0 | ⬜ pending |
| 01-06-03 | 06 | 3 | EXPORT-03 | integration | `pytest tests/test_pdf.py::test_pdf_with_notes -x` | ❌ W0 | ⬜ pending |
| 01-06-04 | 06 | 3 | EXPORT-04 | unit (mock) | `pytest tests/test_pptx.py::test_single_browser_context -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_code_block.py` — stubs for MEDIA-01
- [ ] `tests/test_fragments.py` — stubs for MEDIA-02
- [ ] `tests/test_mermaid.py` — stubs for MEDIA-03
- [ ] `tests/test_video.py` — stubs for MEDIA-04
- [ ] `tests/test_map.py` — stubs for MEDIA-05
- [ ] `tests/test_custom_style.py` — stubs for MEDIA-06
- [ ] `tests/test_toc.py` — stubs for MEDIA-07
- [ ] `tests/test_export_sentinel.py` — stubs for EXPORT-01
- [ ] Expand `tests/test_pptx_native.py` with `TestTitleLayout`, `TestTwoColumnLayout`, `TestStatGridLayout`, `TestThreeColumnLayout` — EXPORT-02
- [ ] Expand `tests/test_pdf.py` with `test_pdf_with_notes` — EXPORT-03
- [ ] Expand `tests/test_pptx.py` with `test_single_browser_context` — EXPORT-04

*Note: 137 existing tests cover the v0.2.0 baseline. All new tests are additive.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Fragment keyboard navigation feels like PowerPoint | MEDIA-02 | UX feel requires human judgment | Open built HTML, press right arrow through fragments, verify reveal order |
| Leaflet tiles load in Playwright file:// context | MEDIA-05 | Browser security context issue | Run `pf pptx` with a map slide, verify tiles render in output |
| YouTube/Vimeo thumbnail quality in PPTX | MEDIA-04 | Visual quality judgment | Build PPTX with video slide, open in PowerPoint, verify thumbnail |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
