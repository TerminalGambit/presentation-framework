---
phase: 01-rich-media-export-polish
plan: 01
subsystem: core-infrastructure
tags: [jinja2, python, highlight.js, mermaid, leaflet, json-schema, pytest]

# Dependency graph
requires: []
provides:
  - Schema validation for 5 new layout names (code, mermaid, video, map, toc)
  - _scan_features() CDN auto-detection in PresentationBuilder
  - Conditional CDN injection for Highlight.js, Mermaid.js, Leaflet in base template
  - Universal data-pf-ready sentinel on all rendered slides
  - Per-slide CSS injection via slide.style key
  - Block type dispatch stubs for code/mermaid/video/map in two-column and three-column
  - Stub partial templates for all 4 new rich media block types
  - Stub layout templates for all 5 new layout names
  - Analyzer height estimates for code (120px), mermaid (200px), video (180px), map (200px)
affects: [01-02, 01-03, 01-04, 01-05, 01-06]

# Tech tracking
tech-stack:
  added: [highlight.js 11.11.1, mermaid.js 11.12.0, leaflet 1.9.4]
  patterns:
    - CDN feature flags scanned from slides before render loop then injected into template context
    - data-pf-ready sentinel pattern for export synchronization (sync for static, async for mermaid)
    - Stub layout + partial templates created upfront so Wave 2 plans can flesh out independently
    - SIZE_MODEL dict in analyzer.py extended with new block types using base/per_item pattern

key-files:
  created:
    - templates/partials/code-block.html.j2
    - templates/partials/mermaid-block.html.j2
    - templates/partials/video-block.html.j2
    - templates/partials/map-block.html.j2
    - templates/layouts/code.html.j2
    - templates/layouts/mermaid.html.j2
    - templates/layouts/video.html.j2
    - templates/layouts/map.html.j2
    - templates/layouts/toc.html.j2
    - tests/test_foundation.py
  modified:
    - pf/schema.json
    - pf/builder.py
    - pf/analyzer.py
    - templates/base.html.j2
    - templates/layouts/two-column.html.j2
    - templates/layouts/three-column.html.j2

key-decisions:
  - "Stub layout templates created for all 5 new layouts (not just partials) so render_slide() doesn't fail when test slides use new layout names"
  - "THEME_BASE fixture with fonts key required in tests — base.html.j2 accesses theme.fonts.heading which fails on dict without fonts"
  - "data-pf-ready sentinel: mermaid sets it after mermaid.run() completes; all others set it synchronously on DOMContentLoaded"
  - "CDN auto-detection scans layouts AND left/right/columns block types to catch inline rich media in columnar slides"

patterns-established:
  - "feature flag pattern: _scan_features() → features dict → template context → {% if features.X %} CDN injection"
  - "sentinel pattern: data-pf-ready on body signals PDF export that async content has settled"
  - "stub-first pattern: create minimal stub templates before Wave 2 plans to avoid TemplateNotFound errors"

requirements-completed:
  - MEDIA-06

# Metrics
duration: 30min
completed: 2026-03-06
---

# Phase 01 Plan 01: Rich Media Foundation Infrastructure Summary

**CDN auto-detection, data-pf-ready sentinel, per-slide CSS injection, and block type dispatch stubs for Highlight.js/Mermaid.js/Leaflet — foundation enabling all Phase 1 Wave 2 plans**

## Performance

- **Duration:** ~30 min
- **Started:** 2026-03-06T08:24:00Z
- **Completed:** 2026-03-06T08:54:47Z
- **Tasks:** 2
- **Files modified:** 16 (6 modified, 10 created)

## Accomplishments

- Schema extended with 5 new layout names and `style`/`fragment` slide properties; all 16 layout names pass validation
- `_scan_features()` scans all slide layouts and block types to determine CDN needs; Highlight.js, Mermaid.js, Leaflet injected only when needed
- Universal `data-pf-ready` attribute on `<body>` synchronizes PDF/PPTX export with async content settling
- All 14 foundation tests pass; full suite at 151 tests with no regressions
- 9 stub templates (4 partials + 5 layouts) created so Wave 2 plans can build independently without file conflicts

## Task Commits

1. **Task 1: Schema + Builder infrastructure** - `7c15477` (feat)
2. **Task 2: Block type dispatch + foundation tests** - `ba83a4d` (feat)

## Files Created/Modified

- `pf/schema.json` - Added code, mermaid, video, map, toc to layout enum; added style and fragment properties
- `pf/builder.py` - Added `_scan_features()`, updated `render_slide()` signature, added features to build loop
- `pf/analyzer.py` - Added height estimates for code (120px), mermaid (200px), video (180px), map (200px)
- `templates/base.html.j2` - Added conditional CDN blocks, data-pf-ready sentinel, slide.style injection
- `templates/layouts/two-column.html.j2` - Added code/mermaid/video/map dispatch to left and right loops
- `templates/layouts/three-column.html.j2` - Added code/mermaid/video/map dispatch to column loop
- `templates/partials/code-block.html.j2` - Stub macro: pre/code with language class, optional caption
- `templates/partials/mermaid-block.html.j2` - Stub macro: .mermaid div for Mermaid.js rendering
- `templates/partials/video-block.html.j2` - Stub macro: data-video-url placeholder div
- `templates/partials/map-block.html.j2` - Stub macro: pf-map-container div with id and height
- `templates/layouts/code.html.j2` - Stub layout extending base, uses code_block partial
- `templates/layouts/mermaid.html.j2` - Stub layout extending base, uses mermaid_block partial
- `templates/layouts/video.html.j2` - Stub layout extending base, uses video_block partial
- `templates/layouts/map.html.j2` - Stub layout extending base, uses map_block partial
- `templates/layouts/toc.html.j2` - Stub layout with numbered list items
- `tests/test_foundation.py` - 14 tests covering schema, auto-detect, sentinel, per-slide CSS, CDN injection, analyzer

## Decisions Made

- Created stub layout templates (not just partials) for all 5 new layouts so the CDN test calling `render_slide()` with `code` layout doesn't raise `TemplateNotFound`
- Tests require THEME_BASE dict including `fonts` key because `base.html.j2` accesses `theme.fonts.heading` — minimal theme configs without fonts cause template errors
- Mermaid sets `data-pf-ready` itself (after `mermaid.run()` completes async); all other content sets it synchronously via `DOMContentLoaded`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Created stub layout templates for new layout names**
- **Found during:** Task 2 (foundation tests)
- **Issue:** Test `test_code_cdn_injected_when_code_feature` calls `render_slide()` with layout `code` — no `code.html.j2` template exists so it raises `TemplateNotFound` / `ClickException`
- **Fix:** Created minimal stub layout templates for all 5 new layouts (code, mermaid, video, map, toc) extending `base.html.j2` and using their respective partials
- **Files modified:** templates/layouts/code.html.j2, mermaid.html.j2, video.html.j2, map.html.j2, toc.html.j2
- **Verification:** Tests pass; `render_slide()` resolves all new layout names
- **Committed in:** ba83a4d (Task 2 commit)

**2. [Rule 1 - Bug] Fixed test configs missing fonts key in theme**
- **Found during:** Task 2 (running foundation tests)
- **Issue:** Plan's test code used `{"primary": ..., "accent": ...}` as theme but `base.html.j2` accesses `theme.fonts.heading` — Jinja2 raises `AttributeError` on `NoneType`
- **Fix:** Added `THEME_BASE` constant with full theme dict including fonts, used in all rendering tests
- **Files modified:** tests/test_foundation.py
- **Verification:** All 14 foundation tests pass
- **Committed in:** ba83a4d (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Both fixes necessary for tests to run. No scope creep — stubs are Wave 2 starting points.

## Issues Encountered

None — both deviations were caught during first test run and fixed immediately.

## Next Phase Readiness

- Wave 2 plans (01-02 through 01-06) can now build in parallel without file conflicts
- All stub templates are ready to be fleshed out by their respective plans
- CDN injection infrastructure is in place; Wave 2 plans just need to populate the layout-specific templates
- The `data-pf-ready` sentinel is in place for the PDF export fix (EXPORT-01)

---
*Phase: 01-rich-media-export-polish*
*Completed: 2026-03-06*
