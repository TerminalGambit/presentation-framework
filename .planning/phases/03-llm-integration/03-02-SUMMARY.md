---
phase: 03-llm-integration
plan: 02
subsystem: optimizer
tags: [content-density, split-slide, layout-analyzer, overflow-detection]

# Dependency graph
requires:
  - phase: 03-llm-integration
    provides: LayoutAnalyzer.estimate_block_height(), USABLE_HEIGHT, COLUMN_GAP, COLUMNAR_LAYOUTS
provides:
  - "split_slide() function that redistributes overflowing slide content into multiple non-overflowing slides"
  - "_fit_split() helper returning (fits, remainder) tuples from block lists"
  - "_has_content() predicate for filtering empty slide outcomes"
affects: [03-04-mcp-optimize-tool, future-llm-optimizer-api]

# Tech tracking
tech-stack:
  added: []
  patterns: [copy.deepcopy for non-mutating slide transformations, _fit_split greedy prefix accumulation]

key-files:
  created:
    - pf/optimizer.py
    - tests/test_optimizer.py
  modified: []

key-decisions:
  - "data-table split operates at the section level (not row level) — each section is a split unit"
  - "Single oversized block (first block exceeds USABLE_HEIGHT) passes through unchanged rather than producing empty slide"
  - "_fit_split greedy prefix: walk blocks accumulating height, split at first block that would exceed USABLE_HEIGHT"
  - "stat-grid treated like three-column (columns list) rather than two-column (left/right) for split"
  - "Non-columnar layouts (title, section, quote, image, timeline, closing) returned unchanged"

patterns-established:
  - "Slide dict mutation avoided by using copy.deepcopy(slide) before modifying split outputs"
  - "Continuation slides get '(cont.)' appended to existing subtitle or set as subtitle if absent"
  - "split_slide returns [slide] unchanged (same object) when no split is needed"

requirements-completed: [LLM-05]

# Metrics
duration: 2min
completed: 2026-03-06
---

# Phase 3 Plan 02: Slide Content Optimizer Summary

**Pure-Python split_slide() optimizer that redistributes overflowing columnar slide blocks into two non-overflowing slides using LayoutAnalyzer height estimates**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-06T20:21:47Z
- **Completed:** 2026-03-06T20:23:55Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Created `pf/optimizer.py` with `split_slide()`, `_fit_split()`, `_has_content()`, and `_set_continuation_subtitle()` helpers
- Handles two-column, three-column, data-table, and stat-grid layouts with layout-specific splitting logic
- Edge cases covered: single oversized block stays in one slide, empty columns filtered out, non-columnar layouts pass through unchanged
- 11 comprehensive tests covering all layouts, edge cases, and invariants (original non-mutation, title preservation, subtitle continuation)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create pf/optimizer.py with split_slide algorithm** - `066a51a` (feat)
2. **Task 2: Write comprehensive tests for optimizer** - `34639b0` (test)

**Plan metadata:** (docs commit follows)

## Files Created/Modified
- `pf/optimizer.py` - split_slide() entry point and algorithm helpers (235 lines)
- `tests/test_optimizer.py` - 11 tests covering all layouts and edge cases (236 lines)

## Decisions Made
- **data-table split at section level:** Each section in a data-table is treated as an atomic split unit. The LayoutAnalyzer wraps each section as a single-item column — so overflow triggers when a section individually exceeds USABLE_HEIGHT (e.g., a table with 20 rows at 725px). Splitting distributes sections between slide_a and slide_b.
- **Single oversized block stays in one slide:** When the very first block in a column exceeds USABLE_HEIGHT, `_fit_split` returns `(blocks, [])` rather than `([], blocks)` — avoids producing an empty slide_a while the oversized content sits in slide_b.
- **stat-grid treated like three-column:** stat-grid uses `columns` list (like three-column) rather than `left`/`right` keys (like two-column). The split logic branches accordingly.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `pf/optimizer.py` is ready for Plan 03-04 to expose `split_slide` as an `optimize_slide` MCP tool
- All 411 tests passing after addition of optimizer module and tests

---
*Phase: 03-llm-integration*
*Completed: 2026-03-06*
