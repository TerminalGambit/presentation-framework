---
phase: 02-plugin-ecosystem
plan: 01
subsystem: plugin-registry
tags: [importlib.metadata, jinja2, ChoiceLoader, entry-points, plugin-discovery]

# Dependency graph
requires:
  - phase: 01-rich-media-export-polish
    provides: PresentationBuilder with complete layout set and test infrastructure
provides:
  - PluginRegistry class with entry point and local directory discovery
  - ChoiceLoader-based template resolution in PresentationBuilder
  - Relaxed schema accepting any string layout name
  - 22 comprehensive tests for plugin discovery and backward compatibility
affects:
  - 02-02 (layout plugins use PluginRegistry for discovery)
  - 02-03 (data source plugins use DataSourcePlugin dataclass + PluginCredentialError)
  - 02-04 (theme plugins use ThemePlugin dataclass)

# Tech tracking
tech-stack:
  added: [importlib.metadata (stdlib entry_points), jinja2.ChoiceLoader]
  patterns:
    - Entry-point plugin discovery via importlib.metadata (not pkg_resources)
    - ChoiceLoader search order: plugin dirs first, core templates last
    - LocalLayoutPlugin for zero-install local templates in <project>/layouts/
    - Registry discover() is idempotent and safe to call at builder startup

key-files:
  created:
    - pf/registry.py
    - tests/test_registry.py
  modified:
    - pf/builder.py
    - pf/schema.json
    - tests/test_schema.py
    - tests/test_foundation.py

key-decisions:
  - "PluginRegistry.discover() called in PresentationBuilder.__init__ with project_dir=config_path.parent — automatic, zero-config for users"
  - "ChoiceLoader puts plugin template dirs before core — plugins can override or extend, not just add"
  - "LocalLayoutPlugin parent's parent added to FileSystemLoader so 'layouts/<name>.html.j2' resolves relative to project root"
  - "Schema layout enum removed — type: string only — plugin layout names pass schema validation"
  - "Broken entry points emit warnings.warn() but do not crash the registry — defensive discovery"

patterns-established:
  - "Plugin discovery: importlib.metadata.entry_points(group='pf.<type>') — never pkg_resources"
  - "Template resolution: ChoiceLoader with core always last — additive plugin model"
  - "Local plugins: project layouts/ dir auto-scanned — no pip install required for prototyping"
  - "Registry integration: builder accepts optional registry arg for dependency injection in tests"

requirements-completed: [PLUG-01]

# Metrics
duration: 4min
completed: 2026-03-06
---

# Phase 02 Plan 01: Plugin Registry Foundation Summary

**PluginRegistry with importlib.metadata entry point discovery, local layouts/ scanning, and ChoiceLoader template resolution integrated into PresentationBuilder — zero config for users, fully backward compatible**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-06T13:47:17Z
- **Completed:** 2026-03-06T13:51:00Z
- **Tasks:** 2 completed
- **Files modified:** 6

## Accomplishments

- Created `pf/registry.py` with `PluginRegistry`, four plugin dataclasses (`LayoutPlugin`, `LocalLayoutPlugin`, `ThemePlugin`, `DataSourcePlugin`), and `PluginCredentialError`
- Integrated registry into `PresentationBuilder.__init__` — builder now uses `ChoiceLoader` instead of bare `FileSystemLoader`, enabling transparent plugin template resolution
- Relaxed `pf/schema.json` layout field from enum to `{"type": "string"}` so plugin layout names pass schema validation
- Added 22 tests covering entry point discovery (mocked), local directory scanning, ChoiceLoader integration, broken plugin warning behavior, backward compatibility, and schema relaxation

## Task Commits

Each task was committed atomically:

1. **Task 1: Create pf/registry.py** - `78ccc0b` (feat)
2. **Task 2: Integrate registry into builder, relax schema, write tests** - `658de40` (feat)

## Files Created/Modified

- `pf/registry.py` - PluginRegistry class, all plugin dataclasses, PluginCredentialError, discover() and get_template_loader()
- `pf/builder.py` - Import ChoiceLoader/PluginRegistry, accept optional registry arg, use registry.get_template_loader() in __init__, include plugin names in render_slide error path
- `pf/schema.json` - Layout field changed from enum to type:string
- `tests/test_registry.py` - 22 new tests (created)
- `tests/test_schema.py` - test_invalid_layout_name renamed and updated to reflect enum removal
- `tests/test_foundation.py` - test_schema_includes_new_layouts updated to verify enum was removed

## Decisions Made

- Used `importlib.metadata.entry_points()` (stdlib) not `pkg_resources` — forward-compatible with Python 3.12+ and the modern packaging ecosystem
- `ChoiceLoader` search order: plugin-specific `FileSystemLoader`s first, core templates last — plugins can override built-in layouts if needed
- `LocalLayoutPlugin` adds `template_path.parent.parent` to the loader so the `"layouts/<name>.html.j2"` path pattern Jinja2 uses is preserved
- Builder always initializes its own `PluginRegistry` if none is provided — backward-compatible, zero new required arguments
- `discover()` calls all three discovery methods — layout, theme, datasource — in a single call from `__init__`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated two existing tests broken by schema enum removal**
- **Found during:** Task 2 (full test suite run after schema change)
- **Issue:** `test_foundation.py::test_schema_includes_new_layouts` accessed `schema["layout"]["enum"]` which no longer exists. `test_schema.py::test_invalid_layout_name` expected validation errors for "nonexistent" layout which now passes.
- **Fix:** Updated both tests to assert the new correct behavior — schema accepts any string layout name, no enum present.
- **Files modified:** `tests/test_foundation.py`, `tests/test_schema.py`
- **Verification:** All 280 tests pass after fix
- **Committed in:** `658de40` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - existing tests reflected old enum behavior)
**Impact on plan:** Fix was necessary for test suite integrity; the schema change was the intended change, tests needed updating to match.

## Issues Encountered

None — implementation matched plan specification exactly. All 280 existing tests pass, 22 new tests pass.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Registry foundation is complete and functional — all Phase 02 plans (02-02 through 02-05) can proceed
- `PluginRegistry` is importable and documented with clear contracts for each plugin type
- `ChoiceLoader` is in place — layout plugin templates will resolve automatically once plugins register their entry points
- Blocker: Google Sheets OAuth2 credential pattern for data source plugins (PLUG-03) remains unresolved — needs separate research before 02-03 begins

---
*Phase: 02-plugin-ecosystem*
*Completed: 2026-03-06*
