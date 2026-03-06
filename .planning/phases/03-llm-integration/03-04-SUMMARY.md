---
phase: 03-llm-integration
plan: "04"
subsystem: mcp-tools
tags: [mcp, instructor, optimizer, accessibility, multi-agent, workflow]

# Dependency graph
requires:
  - phase: 03-llm-integration
    plan: "02"
    provides: split_slide() for optimize_slide MCP tool
  - phase: 03-llm-integration
    plan: "03"
    provides: generate_presentation MCP tool, instructor lazy-import pattern
  - phase: 03-llm-integration
    plan: "05"
    provides: check_slide_dir(), AccessibilityWarning dataclass

provides:
  - "pf/mcp_server.py: optimize_slide MCP tool delegating to split_slide()"
  - "pf/mcp_server.py: suggest_layout MCP tool with instructor lazy import and graceful fallback"
  - "pf/mcp_server.py: check_accessibility_output MCP tool delegating to check_slide_dir()"
  - "pf/mcp_server.py: MULTI_AGENT_WORKFLOW constant documenting the 5-step agent pattern"
  - "tests/test_mcp_server.py: TestOptimizeSlide, TestSuggestLayout, TestCheckAccessibilityOutput"
  - "tests/test_multiagent_workflow.py: 7 smoke tests covering the full workflow sequence"

affects: [agent-usage, mcp-clients, multi-agent-orchestration]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "YAML string input/output for MCP tools that accept/return slide dicts"
    - "Lazy import inside MCP tool function for optional instructor dependency"
    - "Inline Pydantic models (SlideSuggestion, SuggestionList) defined inside tool function body"
    - "Module-level MULTI_AGENT_WORKFLOW constant for agent discovery via MCP introspection"

key-files:
  created:
    - tests/test_multiagent_workflow.py
  modified:
    - pf/mcp_server.py
    - tests/test_mcp_server.py

key-decisions:
  - "optimize_slide accepts YAML string (not dict) — MCP tools are JSON-RPC; passing YAML string keeps the tool interoperable with any client"
  - "suggest_layout defines SlideSuggestion/SuggestionList inline — avoids polluting llm_schemas.py with non-layout models"
  - "check_accessibility_output uses lazy import from pf.accessibility — consistent with existing tool pattern, accessibility module is always present"
  - "MULTI_AGENT_WORKFLOW as module-level string constant — discoverable via MCP introspection and readable in tests"

patterns-established:
  - "optimize_slide returns {slides, count, was_split} metadata — richer than raw list, gives clients split decision at a glance"
  - "check_accessibility_output converts AccessibilityWarning dataclasses to plain dicts — JSON-serializable for MCP protocol"
  - "Multi-agent workflow smoke test uses _write_minimal_presentation helper to share fixture setup across all 7 test functions"

requirements-completed: [LLM-03, LLM-04, LLM-05, LLM-06]

# Metrics
duration: 2min
completed: 2026-03-06
---

# Phase 3 Plan 04: MCP Tool Surface Completion Summary

**Three new MCP tools (optimize_slide, suggest_layout, check_accessibility_output) and a documented multi-agent workflow constant, completing the full LLM integration MCP tool surface**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-03-06T20:33:33Z
- **Completed:** 2026-03-06T20:35:44Z
- **Tasks:** 2
- **Files modified:** 3 (pf/mcp_server.py, tests/test_mcp_server.py, tests/test_multiagent_workflow.py)

## Accomplishments

- Added `optimize_slide` MCP tool to `pf/mcp_server.py`: accepts a YAML string for a single slide, calls `split_slide()` from `pf/optimizer.py`, returns `{slides, count, was_split}` metadata. Handles invalid YAML with a graceful error dict.
- Added `suggest_layout` MCP tool to `pf/mcp_server.py`: uses `instructor` (lazy import with ImportError guard) to suggest next slides given the current deck YAML and topic. Returns `{suggestions: [{layout, title, reasoning}]}` or `{error}` on failure.
- Added `check_accessibility_output` MCP tool to `pf/mcp_server.py`: validates the output directory exists, calls `check_slide_dir()` from `pf/accessibility.py`, converts `AccessibilityWarning` dataclasses to plain JSON-serializable dicts. Returns `{pass, warning_count, warnings}`.
- Added `MULTI_AGENT_WORKFLOW` string constant documenting the 5-step RESEARCHER -> REVIEWER -> OPTIMIZER -> BUILDER -> AUDITOR pattern with optional enhancement steps.
- Added `TestOptimizeSlide` (3 tests), `TestSuggestLayout` (2 tests), `TestCheckAccessibilityOutput` (3 tests) to `tests/test_mcp_server.py`.
- Created `tests/test_multiagent_workflow.py` with 7 smoke tests: workflow documentation validation, layout listing, get-examples loop, optimize step, build step, accessibility audit step, and full end-to-end sequence test.
- Test suite grew from 433 to 449 tests — all pass.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add optimize_slide, suggest_layout, check_accessibility_output MCP tools** - `ca9fd2d` (feat)
2. **Task 2: Write tests for new MCP tools and multi-agent workflow** - `fa68c0b` (test)

## Files Created/Modified

- `pf/mcp_server.py` — optimize_slide, suggest_layout, check_accessibility_output tools + MULTI_AGENT_WORKFLOW constant (+169 lines)
- `tests/test_mcp_server.py` — TestOptimizeSlide, TestSuggestLayout, TestCheckAccessibilityOutput added to imports and file (+63 lines)
- `tests/test_multiagent_workflow.py` — 7 workflow smoke tests created (186 lines)

## Decisions Made

- **optimize_slide accepts YAML string not dict:** MCP tools communicate over JSON-RPC where structured types must be string-serialized. Accepting a YAML string for the slide keeps the tool interoperable with any MCP client without requiring the client to match Python dict conventions.
- **suggest_layout defines models inline:** `SlideSuggestion` and `SuggestionList` are defined inside the `suggest_layout` function body rather than in `pf/llm_schemas.py`. These models are MCP-tool-specific response models, not layout schema models — mixing them would pollute the layout schema registry.
- **check_accessibility_output lazy-imports pf.accessibility:** Consistent with the lazy-import pattern established in Plan 03. While accessibility.py is always installed (stdlib-only), the pattern prevents circular import risks and keeps the import surface predictable.
- **MULTI_AGENT_WORKFLOW as module-level constant:** Discoverable via MCP introspection, readable in tests, and visible to any agent that imports the module. A docstring-only approach would be hidden from runtime introspection.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

- `optimize_slide`, `check_accessibility_output`, and `MULTI_AGENT_WORKFLOW` work without any extras.
- `suggest_layout` requires `pip install 'pf[llm]'` for LLM-backed suggestions; without it, returns `{"error": "LLM features require: pip install 'pf[llm]'"}`.

## Next Phase Readiness

- MCP tool surface for LLM integration is now complete: generate_presentation, get_layout_schema, optimize_slide, suggest_layout, check_accessibility_output, build_presentation, validate_config, check_contrast, list_layouts, get_layout_example, init_presentation — 11 tools total.
- All 4 requirements (LLM-03, LLM-04, LLM-05, LLM-06) are satisfied.
- The multi-agent workflow is documented and smoke-tested against the real tool chain.
- Phase 03 LLM integration is complete.

## Self-Check: PASSED

- `pf/mcp_server.py` (contains optimize_slide): FOUND
- `pf/mcp_server.py` (contains suggest_layout): FOUND
- `pf/mcp_server.py` (contains check_accessibility_output): FOUND
- `pf/mcp_server.py` (contains MULTI_AGENT_WORKFLOW): FOUND
- `tests/test_mcp_server.py` (contains TestOptimizeSlide): FOUND
- `tests/test_multiagent_workflow.py`: FOUND
- Commit `ca9fd2d`: FOUND
- Commit `fa68c0b`: FOUND
- 449 tests: all passed

---
*Phase: 03-llm-integration*
*Completed: 2026-03-06*
