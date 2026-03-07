---
phase: 02-plugin-ecosystem
plan: 02
subsystem: plugin
tags: [jinja2, css-isolation, plugin-system, template-inheritance, choiceloader]

# Dependency graph
requires:
  - phase: 02-plugin-ecosystem
    plan: 01
    provides: PluginRegistry with ChoiceLoader, LayoutPlugin/LocalLayoutPlugin dataclasses, registry.discover()

provides:
  - Plugin CSS auto-copied to theme/plugins/{name}.css during build
  - base.html.j2 conditionally injects <link> tags for plugin CSS
  - render_slide() accepts plugin_css list for template context
  - 4 new tests covering template inheritance, CSS injection, CSS isolation, no-plugin baseline

affects:
  - 02-03 (data source plugins will also need plugin CSS in build pipeline)
  - 02-04 (any plan that builds on plugin output directory structure)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "plugin_css_paths pre-computed before render loop, actual copy deferred to after shutil.copytree"
    - "CSS isolation via .pf-layout-{name} class prefix convention (declared in plugin template, not enforced by framework)"
    - "No theme/plugins/ directory created when no plugins present (clean baseline builds)"

key-files:
  created:
    - .planning/phases/02-plugin-ecosystem/02-02-SUMMARY.md
  modified:
    - pf/builder.py
    - templates/base.html.j2
    - tests/test_registry.py

key-decisions:
  - "plugin_css_paths pre-computed before render loop so all slides get identical <link> tags without a second registry scan"
  - "CSS isolation via class prefix convention (.pf-layout-{name}) — framework injects links in all slides, scoping is by CSS selector not by per-slide filtering"
  - "No theme/plugins/ directory created when no plugins present — avoids empty dirs in clean builds"
  - "LayoutPlugin with multiple css_files collapses to one output file per plugin (first existing file wins in pre-scan, last wins in copy loop) — acceptable for plan scope"

patterns-established:
  - "Plugin CSS test pattern: create layouts/name.html.j2 + layouts/name.css in tmp_path, build, assert theme/plugins/name.css and <link> in HTML"
  - "Template inheritance test pattern: plugin template with {% extends base.html.j2 %}, assert VARIANT CONTENT + <!DOCTYPE html> both present"

requirements-completed: [PLUG-05, PLUG-06]

# Metrics
duration: 6min
completed: 2026-03-06
---

# Phase 02 Plan 02: Plugin CSS Isolation Summary

**Plugin CSS isolation via theme/plugins/ output directory, ChoiceLoader template inheritance, and conditional base.html.j2 link injection — 4 new tests covering all behaviors**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-06T13:54:01Z
- **Completed:** 2026-03-06T14:00:12Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Plugin CSS files (from LocalLayoutPlugin and LayoutPlugin) are auto-copied to `output/theme/plugins/{name}.css` during every build
- `base.html.j2` conditionally injects `<link>` tags for each plugin CSS file so all slides get consistent loading
- Plugin templates can extend `base.html.j2` (or any core template) via Jinja2 template inheritance through the existing ChoiceLoader
- 4 passing tests validate: template inheritance, CSS injection into output, CSS isolation via class prefix, no-plugin baseline

## Task Commits

Each task was committed atomically:

1. **Task 1: Plugin CSS copy logic and base template link injection** - `b00e903` (feat)
2. **Task 2: Tests for template inheritance, CSS injection, and CSS isolation** - `69dd01b` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified
- `pf/builder.py` - Added `plugin_css` param to `render_slide()`, pre-compute `plugin_css_paths` before render loop, copy plugin CSS to `theme/plugins/` after `shutil.copytree`, fixed `LayoutPlugin`/`LocalLayoutPlugin` imports
- `templates/base.html.j2` - Added conditional `{% if plugin_css %}{% for %}` block after `theme/components.css` link
- `tests/test_registry.py` - Added `TestTemplateInheritance`, `TestCSSInjection`, `TestCSSIsolation`, `TestNoPluginCSSWhenNoPlugins` test classes (4 new tests)

## Decisions Made
- CSS isolation via class prefix convention (`.pf-layout-{name}`) — the framework injects links in all slides but CSS scoping is the plugin author's responsibility via class selectors
- `plugin_css_paths` pre-computed before the render loop so all slides get identical `<link>` tags without scanning the registry twice
- `theme/plugins/` directory is only created when plugins with CSS files are present — clean baseline builds have no empty dir
- Missing `LayoutPlugin`/`LocalLayoutPlugin` imports in `builder.py` were fixed as part of Task 2 (Rule 3 - blocking)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Missing LayoutPlugin/LocalLayoutPlugin imports in builder.py**
- **Found during:** Task 2 (running new tests)
- **Issue:** A linter/formatter had changed the `pf.registry` import to only `PluginCredentialError, PluginRegistry`, causing `NameError: name 'LayoutPlugin' is not defined` when the pre-compute block ran
- **Fix:** Added `LayoutPlugin, LocalLayoutPlugin` to the import in `pf/builder.py`
- **Files modified:** `pf/builder.py`
- **Verification:** `python3 -m pytest tests/ -v` — 303 tests pass
- **Committed in:** `69dd01b` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 3 — blocking import error)
**Impact on plan:** Required fix for tests to run. No scope creep.

## Issues Encountered
- None beyond the blocking import deviation documented above.

## User Setup Required
None — no external service configuration required.

## Next Phase Readiness
- Plugin CSS isolation is fully functional; plugin authors can ship companion CSS with their template files
- Template inheritance via ChoiceLoader is proven working with 303 passing tests
- Ready for Plan 03 (data source plugins) — the `theme/plugins/` pipeline is in place and will accommodate ThemePlugin CSS if needed

---
*Phase: 02-plugin-ecosystem*
*Completed: 2026-03-06*
