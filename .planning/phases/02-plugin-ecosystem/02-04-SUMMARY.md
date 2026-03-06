---
phase: 02-plugin-ecosystem
plan: "04"
subsystem: plugin-ecosystem
tags: [datasources, metrics, credentials, registry, builder]

requires:
  - phase: 02-01
    provides: "PluginRegistry with DataSourcePlugin, PluginCredentialError, get_datasource()"

provides:
  - "Builder _resolve_datasources() method: fetches plugin data and merges into self.metrics"
  - "Credential loading from .pf/credentials.json and PF_* env vars (env overrides file)"
  - "Schema optional datasources array with plugin/config/merge_key properties"
  - "14 tests covering all datasource behaviors"

affects:
  - 02-05
  - 02-06
  - phase-03

tech-stack:
  added: []
  patterns:
    - "Datasource resolution runs after load_metrics() and before validate_config() so fetched values are available for {{ metrics.x }} interpolation"
    - "PF_ env var prefix convention for datasource credentials (lowercased on storage)"
    - "merge_key defaults to plugin name when not specified"
    - "PluginCredentialError is fatal (halts build); all other fetch exceptions are non-fatal warnings"

key-files:
  created:
    - tests/test_datasources.py
  modified:
    - pf/builder.py
    - pf/schema.json

key-decisions:
  - "Datasource resolution placed after load_metrics() and before validate_config() — fetched values available for interpolation, schema validation still runs on the YAML structure only"
  - "PluginCredentialError is fatal (halts build with ClickException); general exceptions are non-fatal warnings so builds continue despite flaky APIs"
  - "Env vars use PF_ prefix and are stored lowercased to match lowercase keys in credentials.json"
  - "merge_key defaults to plugin name when not specified — zero-config for simple use cases"

patterns-established:
  - "Credential loading: file (.pf/credentials.json) loaded first, then PF_* env vars override — secure defaults with easy local override"
  - "Datasource plugin test pattern: _make_registry_with_ds(fetch_fn, name) helper + _make_config() to reduce boilerplate across 14 tests"

requirements-completed: [PLUG-03]

duration: 4min
completed: 2026-03-06
---

# Phase 02 Plan 04: Datasource Plugin Resolution Summary

**Builder datasource resolution pipeline: fetch from registered plugins, merge into metrics dict before slide interpolation, with credential loading from env vars and JSON file**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-06T13:54:11Z
- **Completed:** 2026-03-06T13:58:31Z
- **Tasks:** 2
- **Files modified:** 3 (pf/builder.py, pf/schema.json, tests/test_datasources.py)

## Accomplishments

- Added `_resolve_datasources()` to `PresentationBuilder` — fetches from registered datasource plugins, merges results into `self.metrics` before slide rendering
- Credential loading from `.pf/credentials.json` (file, low priority) and `PF_*` env vars (high priority, override file values)
- Schema updated with optional `datasources` array: each entry requires `plugin`, optionally `config` and `merge_key`
- 14 comprehensive tests covering: fetch+merge end-to-end, credential errors halt build, unknown plugins warn+continue, fetch errors warn+continue, backward compat, env var creds, file creds

## Task Commits

1. **Task 1: Add datasource resolution to builder and schema** - `aa84e8c` (feat)
2. **Task 2: Write comprehensive datasource tests** - `cd9dcfb` (test)

## Files Created/Modified

- `pf/builder.py` - Added `_resolve_datasources()` method + datasource step in `build()`; imported `os` and `PluginCredentialError`
- `pf/schema.json` - Added optional `datasources` array property with `plugin`/`config`/`merge_key` items
- `tests/test_datasources.py` - 14 tests across 7 test classes covering all datasource behaviors

## Decisions Made

- Datasource resolution placed after `load_metrics()` and before `validate_config()` so fetched values are available for `{{ metrics.x }}` interpolation while schema validation still runs on YAML structure only
- `PluginCredentialError` is fatal (halts build with `ClickException`); general exceptions are non-fatal warnings so builds continue despite flaky APIs
- Env vars use `PF_` prefix and are stored lowercased to match lowercase keys from credentials.json
- `merge_key` defaults to plugin name when not specified — zero-config for simple use cases

## Deviations from Plan

None — plan executed exactly as written. The plan specified 7 tests; 14 tests were written (2 tests per concept) to achieve better test isolation and coverage. This is within the plan's intent ("comprehensive tests").

## Issues Encountered

None. The file-modification-during-edit tool errors were caused by a linter or file watcher; resolved by reading the file immediately before each edit.

## User Setup Required

None - no external service configuration required. Data source plugin developers must expose credentials via `PF_*` env vars or `.pf/credentials.json`.

## Next Phase Readiness

- Datasource resolution fully operational for plan 02-05 (data source plugin examples/docs) and plan 02-06 (integration testing)
- All 299 tests pass (285 pre-existing + 14 new)
- Full fetch → merge → `{{ metrics.x }}` interpolation chain verified end-to-end

---
*Phase: 02-plugin-ecosystem*
*Completed: 2026-03-06*

## Self-Check: PASSED

- FOUND: pf/builder.py
- FOUND: pf/schema.json
- FOUND: tests/test_datasources.py
- FOUND: .planning/phases/02-plugin-ecosystem/02-04-SUMMARY.md
- FOUND: commit aa84e8c (feat: datasource resolution)
- FOUND: commit cd9dcfb (test: datasource tests)
- Tests: 14/14 passing
