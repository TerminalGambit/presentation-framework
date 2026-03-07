---
phase: 03-llm-integration
plan: 05
subsystem: accessibility
tags: [wcag, aria, high-contrast, html-audit, regex]

# Dependency graph
requires:
  - phase: 01-rich-media-export-polish
    provides: templates/base.html.j2 slide container structure
provides:
  - pf/accessibility.py: check_accessibility(), generate_alt_text(), check_slide_dir(), AccessibilityWarning dataclass
  - theme/base.css: .pf-high-contrast CSS class with WCAG AAA variable overrides
  - templates/base.html.j2: role="region", aria-label, tabindex on slide container + HC toggle button + 'H' keyboard shortcut
affects: [phase-04-platform, mcp_server, cli, agent-usage]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Regex-based HTML accessibility scanning (no BeautifulSoup dependency)"
    - "Filename-derived alt text generation via path stem + title-case"
    - "CSS variable override pattern for high-contrast mode (.slide-container.pf-high-contrast)"
    - "Keyboard shortcut JS handler (IIFE, keydown, classList.toggle) embedded in base template"

key-files:
  created:
    - pf/accessibility.py
    - tests/test_accessibility.py
  modified:
    - templates/base.html.j2
    - theme/base.css

key-decisions:
  - "Regex over BeautifulSoup for HTML scanning — avoids adding a dependency, stdlib only"
  - "Filename-derived alt text is Phase 3 scope — NOT vision-based (vision AI belongs to a later phase)"
  - "High-contrast toggle uses CSS class on slide-container div, not a separate overlay — minimal DOM impact"
  - "Toggle button is visually unobtrusive (opacity 0.4, fixed bottom-right) — doesn't interfere with slide content"
  - "'H' keyboard shortcut skips INPUT/TEXTAREA targets to avoid interfering with text entry"

patterns-established:
  - "Accessibility audit runs post-build on rendered HTML files via check_slide_dir(output_dir)"
  - "WCAG AAA high-contrast: #000000 bg, #FFD700 gold accent, #FFFFFF text — all on slide-container CSS vars"

requirements-completed: [LLM-06]

# Metrics
duration: 2min
completed: 2026-03-06
---

# Phase 03 Plan 05: Accessibility Checker and High-Contrast Mode Summary

**Regex-based HTML accessibility auditor (pf/accessibility.py) with ARIA landmark attributes on all slides and a keyboard-toggled WCAG AAA high-contrast CSS mode**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-03-06T20:21:35Z
- **Completed:** 2026-03-06T20:23:51Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Created `pf/accessibility.py` with `check_accessibility()` (missing alt + aria detection), `generate_alt_text()` (filename fallback), and `check_slide_dir()` batch scanner — all using stdlib `re`, no new dependencies
- Updated `templates/base.html.j2`: added `role="region"`, `aria-label`, `tabindex="0"` to slide container; added `.pf-hc-toggle` button and IIFE JS handler for click + 'H' keyboard shortcut toggling `.pf-high-contrast`
- Added `.slide-container.pf-high-contrast` CSS class to `theme/base.css` with WCAG AAA overrides (black bg, gold accent, white text)
- Added 31 accessibility tests — all pass; full 339-test suite stays green

## Task Commits

Each task was committed atomically:

1. **Task 1: Create pf/accessibility.py and update base template** - `48e39dc` (feat)
2. **Task 2: Add high-contrast CSS mode and write accessibility tests** - `1b5acbf` (feat)

**Plan metadata:** _(docs commit follows)_

## Files Created/Modified
- `pf/accessibility.py` — AccessibilityWarning dataclass, check_accessibility(), generate_alt_text(), check_slide_dir()
- `templates/base.html.j2` — role="region", aria-label, tabindex on slide-container; .pf-hc-toggle button; 'H' keyboard shortcut JS
- `theme/base.css` — .pf-high-contrast class with WCAG AAA CSS variable overrides
- `tests/test_accessibility.py` — 31 tests covering all new functionality

## Decisions Made
- Used stdlib `re` for HTML scanning instead of BeautifulSoup — no new dependencies added to the package
- High-contrast toggle uses `classList.toggle('pf-high-contrast')` on the existing slide container — keeps DOM structure unchanged, no overlay required
- `generate_alt_text()` is filename-based only (Phase 3 scope per research recommendation); vision-based alt text is out of scope until a later phase
- 'H' keyboard shortcut guards against INPUT/TEXTAREA targets so users can still type in forms

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Accessibility checker is ready for use by agents: `check_slide_dir(output_dir)` returns structured `AccessibilityWarning` objects after any build
- MCP `build_presentation` tool can optionally call `check_slide_dir` to surface accessibility warnings alongside content overflow warnings
- High-contrast mode is functional via 'H' key in any built slide — no config required
- All existing functionality is unchanged (339 tests pass)

---
*Phase: 03-llm-integration*
*Completed: 2026-03-06*
