---
phase: 01-rich-media-export-polish
plan: 04
subsystem: templates
tags: [mermaid, leaflet, video, html-templates, jinja2, cdn, javascript]

# Dependency graph
requires:
  - phase: 01-rich-media-export-polish/01-01
    provides: "CDN auto-detection via _scan_features(), stub partials for mermaid/video/map, data-pf-ready sentinel in base.html.j2"

provides:
  - "Full-slide Mermaid diagram layout (.mermaid div, CDN auto-injected, data-pf-ready after mermaid.run())"
  - "Full-slide video embed layout (YouTube click-to-play thumbnail, Vimeo placeholder, MP4 native video)"
  - "Full-slide Leaflet map layout (lat/lng/zoom, markers, OpenStreetMap tiles, data-pf-ready sentinel)"
  - "Refined block partials for all three media types (mermaid-block, video-block, map-block)"
  - "_preprocess_video() and _enrich_video_data() in PresentationBuilder for URL type detection"
  - "_preprocess_video invocation in build() loop for automatic video enrichment"
  - "21 new tests (test_mermaid.py, test_video.py, test_map.py)"
  - "CSS for mermaid centering, video embed with play button overlay, Leaflet map container"

affects:
  - "01-05 (TOC/per-slide CSS) — shares builder.py"
  - "02 (plugins) — rich media types available as block types in all columnar layouts"
  - "PDF/PPTX export — video thumbnails and map screenshots require headless browser"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Builder preprocessing: _preprocess_video enriches slide data before render; templates stay simple"
    - "CDN auto-injection: base.html.j2 conditionally includes CDN based on features dict from _scan_features()"
    - "data-pf-ready sentinel: mermaid sets it after mermaid.run() async; map sets it after whenReady() + 800ms"
    - "Video URL detection: regex-based provider detection (youtube/youtu.be/vimeo/mp4) in builder, not template"

key-files:
  created:
    - templates/layouts/mermaid.html.j2
    - templates/layouts/video.html.j2
    - templates/layouts/map.html.j2
    - tests/test_mermaid.py
    - tests/test_video.py
    - tests/test_map.py
  modified:
    - templates/partials/mermaid-block.html.j2
    - templates/partials/video-block.html.j2
    - templates/partials/map-block.html.j2
    - theme/components.css
    - pf/builder.py

key-decisions:
  - "Mermaid layout uses direct .mermaid div (not macro) — simpler, CDN initialization in base handles the rest"
  - "Video URL detection done in builder.py (_enrich_video_data) not Jinja2 — avoids custom regex filter, cleanly testable"
  - "Map uses OpenStreetMap tiles (no API key required, free, per prior research decision)"
  - "data-pf-ready for map uses map.whenReady() + 800ms timeout to ensure tiles are loaded before PDF export"
  - "Video block partial dispatches on _video_type (preprocessed) not raw URL — templates stay declarative"

patterns-established:
  - "Builder preprocessing pattern: enrich slide data dict before render instead of using complex Jinja2 filters"
  - "CDN-conditional rendering: base.html.j2 checks features.mermaid/features.map/features.code, not template"

requirements-completed: [MEDIA-03, MEDIA-04, MEDIA-05]

# Metrics
duration: 6min
completed: 2026-03-06
---

# Phase 1 Plan 04: Rich Media Embed Types Summary

**Mermaid diagrams, YouTube/Vimeo/MP4 video embeds, and Leaflet maps as full-slide layouts and columnar block types, with builder-side URL preprocessing and 21 tests covering CDN injection, rendering, and data-pf-ready sentinel behavior.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-06T08:58:10Z
- **Completed:** 2026-03-06T09:04:10Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments

- Mermaid layout renders `.mermaid` div, Mermaid CDN auto-injected via base template, `data-pf-ready` set after `mermaid.run()` async completion
- Video layout auto-detects YouTube/Vimeo/MP4 via builder preprocessing; shows click-to-play thumbnail for YouTube, native `<video>` for MP4
- Map layout initializes Leaflet with `lat/lng/zoom`, renders markers with labels, uses free OpenStreetMap tiles, sets `data-pf-ready` after tile load
- All three media types work as both full-slide layouts AND block types inside two-column/three-column layouts
- 21 tests added; full suite at 216 tests passing with no regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Mermaid and Video layouts, partials, and CSS** - `7dc57ce` (feat)
2. **Task 2: Map layout and tests for all three media types** - `59956f6` (feat)

## Files Created/Modified

- `templates/layouts/mermaid.html.j2` - Full-slide Mermaid layout (.mermaid div, CDN via base)
- `templates/layouts/video.html.j2` - Click-to-play video layout (YouTube thumbnail, MP4 native)
- `templates/layouts/map.html.j2` - Leaflet map layout with markers and data-pf-ready sentinel
- `templates/partials/mermaid-block.html.j2` - Block partial with fragment support
- `templates/partials/video-block.html.j2` - Block partial dispatching on _video_type
- `templates/partials/map-block.html.j2` - Block partial with inline Leaflet init script
- `theme/components.css` - Added .pf-mermaid-*, .pf-video-*, .pf-map-* CSS classes
- `pf/builder.py` - Added _preprocess_video(), _enrich_video_data() methods; invoke in build() loop
- `tests/test_mermaid.py` - 6 tests for MEDIA-03 (Mermaid rendering and CDN detection)
- `tests/test_video.py` - 7 tests for MEDIA-04 (video URL detection and layout rendering)
- `tests/test_map.py` - 8 tests for MEDIA-05 (map rendering, markers, CDN, sentinel)

## Decisions Made

- **Builder preprocessing over Jinja2 filters**: Jinja2 has no built-in `regex_replace` filter. Rather than add a custom filter, video URL parsing is done in `_enrich_video_data()` in Python. This keeps templates simple and makes the logic unit-testable.
- **OpenStreetMap tiles**: Free, no API key needed, consistent with research decision.
- **map.whenReady() + 800ms timeout**: The `whenReady` event fires when the map is initialized but tiles may not be visible. The 800ms timeout ensures tiles are at least partially loaded before PDF export.
- **Mermaid layout drops macro import**: The stub layout used a macro wrapper, but the full layout directly writes `<div class="mermaid">`. This is simpler and matches the mermaid.js contract of targeting `.mermaid` elements.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Test helper in plan's verify script used incomplete theme config**
- **Found during:** Task 1 verification
- **Issue:** Plan's inline verification script used `{'primary': '#...', 'accent': '#...'}` without `fonts` sub-dict. Template accesses `theme.fonts.heading` causing `UndefinedError`.
- **Fix:** Test files created with complete theme dict including `fonts` sub-key, matching the pattern used in all other test files.
- **Files modified:** tests/test_mermaid.py, tests/test_video.py, tests/test_map.py
- **Verification:** All 21 tests pass
- **Committed in:** 59956f6 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 bug)
**Impact on plan:** Minor — only affected test helper config, not implementation logic. No scope creep.

## Issues Encountered

- Map layout, partials, test files, and CSS were partially committed by a prior plan execution (docs(01-03) commit `d40ea9a`) that bundled them with documentation updates. Task 2 commit captured the 01-05-SUMMARY.md which was already staged. All artifacts exist correctly in the repository and all tests pass.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All three rich media types (Mermaid, Video, Map) are production-ready
- CDN auto-injection works for mermaid and leaflet; no CDN needed for video (iframe embeds)
- All media types work as both full-slide layouts and inline block types
- Plan 01-05 (TOC layout) and 01-06 (PPTX/PDF export) can proceed
- Export plans (01-06) should note: video thumbnails need click-to-play disabled for PDF; map needs screenshot via Playwright

---
*Phase: 01-rich-media-export-polish*
*Completed: 2026-03-06*

## Self-Check: PASSED

- FOUND: templates/layouts/mermaid.html.j2
- FOUND: templates/layouts/video.html.j2
- FOUND: templates/layouts/map.html.j2
- FOUND: tests/test_mermaid.py
- FOUND: tests/test_video.py
- FOUND: tests/test_map.py
- FOUND: .planning/phases/01-rich-media-export-polish/01-04-SUMMARY.md
- FOUND: commit 7dc57ce (Task 1)
- FOUND: commit 59956f6 (Task 2)
- All 21 media tests pass; 216 total tests passing
