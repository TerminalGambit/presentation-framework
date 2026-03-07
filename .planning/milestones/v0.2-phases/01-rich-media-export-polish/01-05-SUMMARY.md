---
phase: 01-rich-media-export-polish
plan: 05
subsystem: toc-layout
tags: [jinja2, python, pytest, table-of-contents, per-slide-css]

# Dependency graph
requires:
  - 01-01 (schema with toc layout name, per-slide style injection in base.html.j2)
provides:
  - Auto-generated Table of Contents via _generate_toc() scanning section slides
  - toc.html.j2 layout rendering numbered entries with titles and optional subtitles
  - TOC CSS components (.pf-toc, .pf-toc-entry, .pf-toc-number, .pf-toc-title, .pf-toc-subtitle)
  - tests/test_toc.py: 13 tests for TOC generation and rendering (MEDIA-07)
  - tests/test_custom_style.py: 7 tests for per-slide CSS injection (MEDIA-06)
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - TOC auto-generation: _generate_toc() scans slides before render loop; injects into toc layout data
    - Jinja2 dict key access: use slide.data.get('items') not slide.data.items to avoid .items() method collision
    - THEME_BASE fixture pattern: theme dict requires fonts key (established in Plan 01)

key-files:
  created:
    - templates/layouts/toc.html.j2
    - tests/test_toc.py
    - tests/test_custom_style.py
  modified:
    - pf/builder.py
    - theme/components.css

key-decisions:
  - "Use slide.data.get('items') not slide.data.items in Jinja2 to avoid collision with Python dict .items() builtin method"
  - "TOC preprocessing injects into toc slides before the render loop so all toc slides share the same auto-generated entries"
  - "THEME_BASE in tests includes fonts key — required by base.html.j2 which accesses theme.fonts.heading"

# Metrics
duration: 3min
completed: 2026-03-06
---

# Phase 01 Plan 05: TOC Layout and Per-Slide CSS Tests Summary

**Auto-generated Table of Contents scanning section slides into numbered entries with titles/subtitles, plus test coverage for per-slide CSS injection**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-03-06T08:58:22Z
- **Completed:** 2026-03-06T09:01:30Z
- **Tasks:** 2
- **Files modified:** 5 (3 created, 2 modified)

## Accomplishments

- `_generate_toc()` method scans all slides for `layout == "section"` and returns list of `{number, title, subtitle}` dicts
- `build()` preprocesses TOC slides before the render loop — injects auto-generated section entries into `data.items`
- `toc.html.j2` replaces stub with full layout: header partial, numbered entries with `%02d` formatting, subtitles
- TOC CSS added to `components.css`: flex column, accent left border, gold section numbers, clean typography
- 13 TOC tests and 7 per-slide CSS tests all pass; full suite at 195 tests with no regressions

## Task Commits

1. **Task 1: TOC layout, builder method, and CSS** - `ebdfb2f` (feat)
2. **Task 2: TOC and per-slide CSS tests** - `424876e` (test)

## Files Created/Modified

- `pf/builder.py` - Added `_generate_toc()` method and TOC preprocessing in `build()`
- `templates/layouts/toc.html.j2` - Full layout: centered container, bg-pattern, header partial, pf-toc entries loop
- `theme/components.css` - Added .pf-toc, .pf-toc-entry, .pf-toc-number, .pf-toc-text, .pf-toc-title, .pf-toc-subtitle
- `tests/test_toc.py` - 13 tests: section scanning, empty cases, missing number/subtitle, rendering, title in header
- `tests/test_custom_style.py` - 7 tests: style injected, gradient, two-column, multiple slides independent, TOC slide

## Decisions Made

- `slide.data.get('items')` used instead of `slide.data.items` in Jinja2 template — the latter resolves to Python dict's `items()` built-in method, causing a `TypeError: 'builtin_function_or_method' object is not iterable` error
- TOC preprocessing runs before the render loop, so all `toc` layout slides share the same auto-generated entries based on the full deck's section structure
- Tests use `THEME_BASE` dict with `fonts` key (established as required pattern in Plan 01)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed Jinja2 dict.items() method collision in toc.html.j2**
- **Found during:** Task 1 (running verify check)
- **Issue:** Plan's template used `slide.data.items | default([])` — in Jinja2, `.items` attribute lookup on a Python dict returns the built-in `dict.items()` method, not the key `items`. This causes `TypeError: 'builtin_function_or_method' object is not iterable` when Jinja2 tries to iterate it.
- **Fix:** Changed to `(slide.data.get('items') or [])` which correctly calls `.get()` and returns the list value (or empty list if missing)
- **Files modified:** templates/layouts/toc.html.j2
- **Verification:** TOC rendering check passes; all tests pass

**2. [Rule 1 - Bug] Plan's verify script used theme dict without fonts key**
- **Found during:** Task 1 (running verify check from plan)
- **Issue:** Plan's verify script used `{'primary': ..., 'accent': ...}` as theme — `base.html.j2` accesses `theme.fonts.heading` causing `UndefinedError`. This was documented as a known issue in Plan 01's SUMMARY.
- **Fix:** Added complete `fonts` dict to theme in verify and in test fixtures (THEME_BASE pattern)
- **Files modified:** tests/test_toc.py, tests/test_custom_style.py
- **Verification:** All tests pass

---

**Total deviations:** 2 auto-fixed (both Rule 1 bugs)
**Impact on plan:** Both fixes were necessary for correctness; no scope creep.

## Issues Encountered

None beyond the two auto-fixed deviations above.

## Next Phase Readiness

- MEDIA-07 (TOC layout) fully implemented and tested
- MEDIA-06 (per-slide CSS) test coverage added — requirements complete
- All Phase 1 Wave 2 plans can proceed; this plan has no downstream dependencies

---
*Phase: 01-rich-media-export-polish*
*Completed: 2026-03-06*

## Self-Check: PASSED

- FOUND: templates/layouts/toc.html.j2
- FOUND: pf/builder.py (with _generate_toc method)
- FOUND: theme/components.css (with .pf-toc styles)
- FOUND: tests/test_toc.py
- FOUND: tests/test_custom_style.py
- FOUND: 01-05-SUMMARY.md
- FOUND: commit ebdfb2f (Task 1 - TOC layout, builder method, CSS)
- FOUND: commit 424876e (Task 2 - TOC and per-slide CSS tests)
