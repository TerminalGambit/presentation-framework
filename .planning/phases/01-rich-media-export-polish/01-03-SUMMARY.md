---
phase: 01-rich-media-export-polish
plan: 03
subsystem: fragment-reveal
tags:
  - fragments
  - progressive-reveal
  - presenter-experience
  - MEDIA-02
dependency_graph:
  requires:
    - 01-01 (base layout stubs, CDN injection, _scan_features)
  provides:
    - Fragment reveal system (pf-fragment class + JS state machine)
    - challenge_card macro with per-block and per-bullet fragment support
  affects:
    - templates/present.html.j2
    - templates/partials/card.html.j2
    - templates/layouts/two-column.html.j2
    - templates/layouts/three-column.html.j2
    - theme/components.css
tech_stack:
  added: []
  patterns:
    - pf-fragment CSS class: hidden by default (opacity:0, translateY:12px), revealed via JS adding .visible
    - Fragment state machine in navigator JS: intercepts arrow keys before slide advance
    - Dict bullet format: {text, fragment} for per-bullet reveals; plain strings preserved for backward compat
key_files:
  created:
    - tests/test_fragments.py
  modified:
    - theme/components.css
    - templates/present.html.j2
    - templates/partials/card.html.j2
    - templates/layouts/two-column.html.j2
    - templates/layouts/three-column.html.j2
decisions:
  - Fragment state lives in navigator (present.html.j2), not in slide iframes — navigator drives iframe contentDocument directly
  - show() load handler consolidates enableLightbox + enableChartModals + revealAllFragments in one listener
  - Backward nav (left arrow) hides last visible fragment first, then goes to previous slide with all fragments pre-revealed
  - Dict bullet format for per-bullet fragments preserves backward compat: plain strings still render unchanged
metrics:
  duration: "2 minutes"
  tasks_completed: 2
  files_modified: 5
  files_created: 1
  tests_added: 9
  tests_total: 175
  completed_date: "2026-03-06T09:00:54Z"
requirements_satisfied:
  - MEDIA-02
---

# Phase 1 Plan 3: Fragment Reveal System Summary

Fragment reveal system for progressive content builds — keyboard-driven reveal of hidden elements before slide advancement, matching the PowerPoint/reveal.js model.

## What Was Built

### Fragment CSS (`theme/components.css`)
Added `.pf-fragment` class that hides elements with `opacity: 0` and `transform: translateY(12px)`, with smooth 0.35s ease transition. Adding `.visible` class animates to full opacity and zero offset.

### Fragment State Machine (`templates/present.html.j2`)
Added six fragment helper functions:
- `getFragments()` — queries all `.pf-fragment` in current slide iframe
- `getHiddenFragments()` — queries `.pf-fragment:not(.visible)`
- `getVisibleFragments()` — queries `.pf-fragment.visible`
- `revealNextFragment()` — adds `.visible` to first hidden fragment; returns true if one existed
- `hideLastFragment()` — removes `.visible` from last visible fragment; returns true if one existed
- `revealAllFragments()` — pre-reveals all fragments (used for backward navigation)

Updated `next()` / `prev()` to be fragment-aware:
- Right arrow: reveals next hidden fragment first; if none, advances slide
- Left arrow: hides last visible fragment first; if none, goes to previous slide with all fragments pre-revealed

Updated `show()` to accept a `showAllFragments` parameter and consolidate `enableLightbox` + `enableChartModals` into a single `load` event listener per navigation.

### Card Partial (`templates/partials/card.html.j2`)
Updated `challenge_card` macro signature to `challenge_card(icon, title, text, bullets=[], fragment=false)`. When `fragment=true`, adds `pf-fragment` class to the block-level wrapper div. Bullet loop updated to handle both:
- Plain strings: `"Point A"` → renders as before (backward compat)
- Dict bullets: `{"text": "Point A", "fragment": true}` → adds `pf-fragment` class to individual bullet div

### Column Layouts
- `two-column.html.j2`: both left and right column card dispatch now pass `item.fragment | default(false)` to `challenge_card`
- `three-column.html.j2`: inline card div receives `pf-fragment` class when `item.fragment` is truthy

### Tests (`tests/test_fragments.py`)
9 tests across 5 classes:
- `TestBlockFragment` — card with/without fragment, code block with fragment
- `TestBulletFragment` — dict bullets get class, plain strings preserved
- `TestFragmentCSS` — components.css contains required styles
- `TestFragmentNavigator` — present.html.j2 references fragment class
- `TestCardFragmentPartial` — card partial has fragment parameter and dict bullet support

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing] Add fonts key to test helper**
- **Found during:** Task 2 (test run)
- **Issue:** `_render()` helper in test_fragments.py used minimal theme config without `fonts` key, causing template error `'dict object' has no attribute 'fonts'`
- **Fix:** Added `THEME_BASE` constant matching pattern used in `test_code_block.py` — `{"heading": "Playfair Display", "subheading": "Montserrat", "body": "Lato"}`
- **Files modified:** `tests/test_fragments.py`
- **Commit:** d31b293

## Self-Check: PASSED

Files verified:
- FOUND: tests/test_fragments.py
- FOUND: theme/components.css (pf-fragment CSS appended)
- FOUND: templates/present.html.j2 (fragment JS added)
- FOUND: templates/partials/card.html.j2 (fragment param added)
- FOUND: templates/layouts/two-column.html.j2 (fragment dispatch added)
- FOUND: templates/layouts/three-column.html.j2 (fragment class added)

Commits verified:
- FOUND: ce4c3e2 (feat: fragment system implementation)
- FOUND: d31b293 (test: fragment tests)

Test results: 9/9 fragment tests pass, 175/175 total tests pass
