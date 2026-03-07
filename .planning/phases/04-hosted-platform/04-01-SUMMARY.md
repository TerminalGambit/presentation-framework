---
phase: 04-hosted-platform
plan: 01
subsystem: build
tags: [cdn, base-url, asset-paths, html-rewrite, cli, builder]

requires:
  - phase: 03-llm-integration
    provides: "PresentationBuilder.build() pipeline used as base for extension"

provides:
  - "_rewrite_asset_paths(html, base_url) module-level function in pf/builder.py"
  - "base_url parameter on PresentationBuilder.build()"
  - "--base-url CLI option on pf build command"
  - "Unit + integration tests for both"

affects: [04-02, 04-03, 04-04]

tech-stack:
  added: []
  patterns:
    - "Post-process HTML pass: glob(*.html), read, transform, write after all files are written"
    - "Negative lookahead regex for URL scheme skipping: (?!http://|https://|data:|//|#)"

key-files:
  created: []
  modified:
    - "pf/builder.py"
    - "pf/cli.py"
    - "tests/test_builder.py"
    - "tests/test_cli.py"

key-decisions:
  - "Post-processing pass runs after all HTML files are written (not inline during render) — cleaner separation, one glob covers all files"
  - "regex negative lookahead over BeautifulSoup — no added dependency, straightforward for href/src rewriting"
  - "Trailing slash stripped from base_url in _rewrite_asset_paths to prevent double-slash paths"

patterns-established:
  - "Asset rewriting: module-level pure function _rewrite_asset_paths(html, base_url) -> str — testable without builder instance"
  - "Build extension: optional params on build() default to None and are no-ops when omitted — backward compatible"

requirements-completed: [PLAT-06]

duration: 8min
completed: 2026-03-07
---

# Phase 4 Plan 01: Base URL Path Abstraction Summary

**`_rewrite_asset_paths()` post-processor using regex negative lookahead rewrites all relative href/src to absolute CDN URLs, enabling hosted deck deployments with `pf build --base-url https://cdn.example.com`**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-07T15:15:12Z
- **Completed:** 2026-03-07T15:23:00Z
- **Tasks:** 2 completed
- **Files modified:** 4

## Accomplishments

- Module-level `_rewrite_asset_paths(html, base_url)` using `re.sub` with negative lookahead — skips http/https/data://# URLs to prevent double-prefixing CDN-hosted libraries (Google Fonts, jsDelivr, KaTeX, etc.)
- `PresentationBuilder.build()` gains `base_url: str | None = None` parameter; post-processes all `*.html` in output dir when set
- `--base-url` Click option added to `pf build` command; threaded through to `builder.build()`
- 7 tests added: 4 unit tests on `_rewrite_asset_paths` + 3 integration/CLI tests; all 457 tests pass

## Task Commits

Each task was committed atomically:

1. **Task 1: Add _rewrite_asset_paths() and base_url parameter to builder** - `8bc6f7f` (feat)
2. **Task 2: Add --base-url CLI option to pf build command** - `9bc04d3` (feat)

**Plan metadata:** (final docs commit below)

## Files Created/Modified

- `pf/builder.py` — Added `_rewrite_asset_paths()` function and `base_url` param on `build()`
- `pf/cli.py` — Added `--base-url` option to `build` command, passed to `builder.build()`
- `tests/test_builder.py` — Added `TestRewriteAssetPaths` class (4 unit tests) + `test_build_with_base_url` and `test_build_without_base_url` integration tests
- `tests/test_cli.py` — Added `test_build_base_url` and `test_build_no_base_url_default` CLI tests

## Decisions Made

- **Post-processing pass after all HTML written:** Rather than rewriting paths inline during each slide render, the `base_url` pass runs at the end of `build()` as a single glob over `*.html`. This keeps rendering logic clean and ensures present.html (written last) is also covered.
- **Regex over BeautifulSoup:** The `re.sub` approach with a negative lookahead avoids adding a parser dependency while correctly handling the simple `href`/`src` attribute pattern.
- **Trailing slash normalization:** `base_url.rstrip("/")` in `_rewrite_asset_paths` prevents double-slash paths like `https://cdn.example.com//theme/base.css`.

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- `base_url` plumbing is in place; 04-02 through 04-04 can build on `builder.build(base_url=...)` and the `--base-url` CLI flag
- All 457 existing tests passing — no regressions introduced

---
*Phase: 04-hosted-platform*
*Completed: 2026-03-07*

## Self-Check: PASSED

- pf/builder.py: FOUND, contains `_rewrite_asset_paths`
- pf/cli.py: FOUND, contains `base-url` option
- tests/test_builder.py: FOUND, contains test_base_url tests
- tests/test_cli.py: FOUND, contains test_build_base_url
- Commit 8bc6f7f: FOUND
- Commit 9bc04d3: FOUND
