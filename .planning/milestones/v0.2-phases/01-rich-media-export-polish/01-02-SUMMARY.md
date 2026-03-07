---
phase: 01-rich-media-export-polish
plan: 02
subsystem: ui
tags: [highlight.js, code-highlighting, jinja2, html-templates, syntax-highlighting]

# Dependency graph
requires:
  - phase: 01-01
    provides: "_scan_features() CDN detection, stub code.html.j2, stub code-block.html.j2, Highlight.js CDN injection in base.html.j2"
provides:
  - "Full-slide code layout (code.html.j2) with pf-code-fullslide, language class, line numbers, caption"
  - "Refined code-block partial (code-block.html.j2) with language badge for columnar layouts"
  - "Code block CSS in components.css (pf-code-fullslide, pf-code-block, pf-code-lang-badge, pf-code-caption)"
  - "15 tests covering: layout rendering, CDN injection, theme selection, block partial"
affects:
  - "03-mermaid-video-map — establishes pf-X-fullslide CSS pattern used by media layouts"
  - "templates using columnar block dispatch — code-block.html.j2 partial is now production-ready"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "pf-code-fullslide: direct pre/code in layout template (not delegated to partial) for full-slide layouts"
    - "pf-code-lang-badge: positioned absolute top-right language indicator for inline code blocks"
    - "language-{lang} class on code element: Highlight.js auto-processes via hljs.highlightAll()"
    - "data-line-numbers attribute: semantic marker for optional line number plugin support"

key-files:
  created:
    - "tests/test_code_block.py — 15 tests: TestCodeLayout, TestCodeCDN, TestCodeThemeSelection, TestCodeBlockPartial"
  modified:
    - "templates/layouts/code.html.j2 — replaced pf-code-layout stub with pf-code-fullslide direct rendering"
    - "templates/partials/code-block.html.j2 — added language badge, improved caption/line-numbers handling"
    - "theme/components.css — added code block CSS section at end"

key-decisions:
  - "Full-slide layout uses direct pre/code rather than delegating to code-block partial — simpler and avoids macro overhead for the full-slide case"
  - "Language badge only shown when language is explicitly set and not 'auto' — avoids badge noise on auto-detected code"
  - "Test helper _render() requires fonts in THEME_BASE — plan spec omitted fonts key causing UndefinedError, fixed in test helper"

patterns-established:
  - "Full-slide media layout: direct HTML, not via partial — consistent with chart.html.j2 pattern"
  - "Block-level partial macro: adds badge/metadata on top, pre/code block, optional caption below"

requirements-completed:
  - MEDIA-01

# Metrics
duration: 15min
completed: 2026-03-06
---

# Phase 01 Plan 02: Code Syntax Highlighting Summary

**Syntax-highlighted code blocks via Highlight.js: full-slide layout with pf-code-fullslide, inline block partial with language badge, theme-matched CDN (github/github-dark), and 15 tests**

## Performance

- **Duration:** 15 min
- **Started:** 2026-03-06T08:58:11Z
- **Completed:** 2026-03-06T09:13:00Z
- **Tasks:** 2
- **Files modified:** 3 + 1 created

## Accomplishments
- Upgraded `code.html.j2` from stub to full implementation: direct `<pre><code class="language-{lang}">` rendering with optional `data-line-numbers` and caption
- Refined `code-block.html.j2` partial with language badge (`.pf-code-lang-badge`) positioned absolute top-right — only shown when language is explicitly set and not "auto"
- Added complete code block CSS to `components.css`: fullslide container, pre/code typography, language badge, caption, line number counter-reset
- 15 tests covering all MEDIA-01 acceptance criteria: rendering, CDN auto-injection, dark/light theme selection, columnar block dispatch

## Task Commits

Each task was committed atomically:

1. **Task 1: Code layout template and refined code-block partial** - `0919e53` (feat)
2. **Task 2: Code block tests** - `339e2fa` (test)

**Plan metadata:** (docs commit below)

## Files Created/Modified
- `templates/layouts/code.html.j2` - Full-slide code layout: pf-code-fullslide, language class, line numbers, caption
- `templates/partials/code-block.html.j2` - Inline code block macro with language badge for columnar layouts
- `theme/components.css` - Added code block CSS section (pf-code-fullslide, pf-code-block, pf-code-lang-badge, pf-code-caption)
- `tests/test_code_block.py` - 15 tests: layout rendering, CDN injection, theme selection, block partial

## Decisions Made
- Full-slide layout directly renders `<pre><code>` rather than delegating to the `code_block` macro — consistent with `chart.html.j2` pattern, avoids macro overhead for full-slide case
- Language badge only shows when language is explicitly set and not "auto" — reduces visual noise on auto-detected code
- Used `language-{{ item.language | default('') }}` (empty string as fallback) rather than `language-auto` — Highlight.js handles empty class gracefully and auto-detects

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Added fonts key to test helper _render()**
- **Found during:** Task 2 (Code block tests)
- **Issue:** The plan spec's `_render()` helper used a minimal theme config without a `fonts` key. `base.html.j2` accesses `theme.fonts.heading` which raises `jinja2.exceptions.UndefinedError` when fonts is absent
- **Fix:** Added `THEME_BASE` constant with `fonts` key matching pattern used in `test_foundation.py`; merged it into the helper's theme config
- **Files modified:** `tests/test_code_block.py`
- **Verification:** All 15 tests pass with no UndefinedError
- **Committed in:** `339e2fa` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug in plan spec's test helper)
**Impact on plan:** Required fix for tests to run at all. No scope creep — identical test logic, just correct theme config.

## Issues Encountered
- Plan 01-01, 01-03, and 01-05 were already committed before this plan ran. The stub files (`code.html.j2`, `code-block.html.j2`) created in 01-01 provided the correct starting point. CSS from 01-03 (fragment reveal) and 01-05 (TOC) was already in `components.css`, so this plan appended at the correct location.

## Next Phase Readiness
- MEDIA-01 (code syntax highlighting) fully complete — full-slide layout, columnar block type, CDN auto-detection, theme matching
- Ready for Plan 01-03 (Mermaid diagrams) — `pf-X-fullslide` pattern established for media layouts
- `code-block.html.j2` partial is production-ready for use in two-column, three-column, and any future columnar layouts

---
*Phase: 01-rich-media-export-polish*
*Completed: 2026-03-06*
