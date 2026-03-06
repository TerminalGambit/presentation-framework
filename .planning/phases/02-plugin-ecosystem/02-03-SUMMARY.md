---
phase: 02-plugin-ecosystem
plan: 03
subsystem: theme-plugin-system
tags: [theme-plugins, merge-logic, entry-points, deep-merge, schema]

# Dependency graph
requires:
  - phase: 02-plugin-ecosystem
    plan: 01
    provides: PluginRegistry with ThemePlugin dataclass and _discover_themes() method
provides:
  - Theme plugin merge in builder.build() — plugin defaults + user overrides
  - theme.name key in schema.json — enables plugin theme selection in presentation.yaml
  - Theme plugin CSS copy to theme/plugins/ directory
  - 5 new tests covering theme discovery, merge, and schema acceptance
affects:
  - 02-05 (full plugin integration — theme plugins are now usable end-to-end)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Theme merge: {**plugin_defaults, **user_overrides} with special-case deep merge for fonts"
    - "Plugin CSS: base_theme.css_file copied to theme/plugins/ alongside layout plugin CSS"
    - "Graceful degradation: unknown theme names silently ignored, inline values used"

key-files:
  created: []
  modified:
    - pf/builder.py
    - pf/schema.json
    - tests/test_registry.py

key-decisions:
  - "Theme merge order: plugin defaults applied first, then user overrides — user values always win"
  - "Fonts deep-merged independently: plugin provides heading+body, user can override just heading, body preserved"
  - "Unknown theme names silently ignored — graceful degradation, no crash"
  - "Theme merge happens in build() after _warnings, before contrast checks — theme_cfg variable reused for both"
  - "Test configs require fonts key to match real-world usage (base.html.j2 accesses theme.fonts.heading)"

requirements-completed: [PLUG-02]

# Metrics
duration: 4min
completed: 2026-03-06
---

# Phase 02 Plan 03: Theme Plugin System Summary

**Theme plugin merge with plugin defaults < user overrides, deep-merged fonts, theme CSS copy, and 5 passing tests — users can install pip theme packages and reference them by name in presentation.yaml**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-06T13:54:07Z
- **Completed:** 2026-03-06T13:58:05Z
- **Tasks:** 2 completed
- **Files modified:** 3

## Accomplishments

- Added theme plugin merge logic to `build()` in `pf/builder.py`: plugin defaults applied first, then user values override; fonts dict deep-merged so individual font properties can be selectively overridden
- Added theme plugin CSS copy: if `base_theme.css_file` exists and is a file, it's copied to `theme/plugins/` in the output directory
- Added `"name": {"type": "string"}` to the `theme` object in `pf/schema.json` so `theme.name` passes validation
- Added 5 tests to `tests/test_registry.py` covering: entry point discovery, default+override merge behavior, fonts deep-merge, no-name passthrough, unknown name graceful ignore, schema acceptance

## Task Commits

Each task was committed atomically:

1. **Task 1: Theme merge logic and schema.name property** - `1ea4d17` (feat)
2. **Task 2: 5 theme plugin tests** - `cd97b78` (test)

## Files Created/Modified

- `pf/builder.py` — Theme plugin merge block added after `self._warnings`, before contrast checks; theme CSS copy added in plugin CSS section
- `pf/schema.json` — `"name": {"type": "string"}` added to theme properties
- `tests/test_registry.py` — 5 new tests in `TestThemePluginDiscovery` class (27 total)

## Decisions Made

- Theme merge order is plugin defaults then user overrides — this is the "CSS-like" model where the more specific value wins
- Fonts are deep-merged as a special case because themes typically provide all three fonts (heading/subheading/body) but users may only want to override one
- The `theme_name` variable is tracked from the merged `theme_cfg` for use in both the merge section and the CSS copy section (no double `get_theme()` call per build)
- Test configs for full-build tests must include `fonts` key because `base.html.j2` uses `theme.fonts.heading` with Jinja2's attribute access (not item access) on a dict — omitting fonts causes UndefinedError

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed missing fonts key in test configs for full-build tests**
- **Found during:** Task 2 (test run)
- **Issue:** `test_theme_no_name_key_uses_inline` and `test_theme_unknown_name_ignored` used minimal theme dicts without a `fonts` key. `base.html.j2` line 15 uses `theme.fonts.heading` via Jinja2 attribute access — when `fonts` is absent from the dict, Jinja2 raises `UndefinedError: 'dict object' has no attribute 'fonts'` rather than returning `Undefined` (dict attribute access in Jinja2 uses `getattr`, not `getitem`).
- **Fix:** Added complete `fonts: {heading, subheading, body}` to both test theme configs so they match real-world valid configs.
- **Files modified:** `tests/test_registry.py`
- **Committed in:** `cd97b78` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 — test configs were incomplete, missing required fonts key)

## Issues Encountered

None beyond the auto-fixed test config issue above.

## User Setup Required

None — theme plugin usage requires `pip install <theme-package>` by end users, but the framework itself has no new setup requirements.

## Next Phase Readiness

- Theme plugins are fully functional: discovery via entry points, merge with user overrides, CSS copy
- `pf.themes` entry point group is documented and implemented
- Users can create distributable theme packages with `ThemePlugin` dataclass + `pf.themes` entry point
- All 299 tests pass

---
*Phase: 02-plugin-ecosystem*
*Completed: 2026-03-06*
