---
phase: 03-llm-integration
plan: "01"
subsystem: api
tags: [pydantic, json-schema, llm, structured-output, instructor]

requires:
  - phase: 02-plugin-ecosystem
    provides: PluginRegistry, LayoutPlugin, and complete layout set (11 layouts) to model

provides:
  - "pf/llm_schemas.py: 11 per-layout Pydantic v2 models with maxItems/maxLength constraints"
  - "PresentationOutput wrapper model (yaml_config + metrics fields) for LLM generation pipeline"
  - "get_layout_schema(name) and get_all_schemas() lookup functions for instructor integration"
  - "ContentBlock discriminated union for typed column content"
  - "Block-level models: CardBlock, SolutionBoxBlock, StatGridBlock, TableBlock, DistBarBlock, ValBarBlock, InsightBlock"

affects:
  - "03-02: instructor integration uses these as response_model"
  - "03-03: MCP get_layout_schema tool exposes these schemas to LLM agents"

tech-stack:
  added: [pydantic v2]
  patterns:
    - "Field(max_length=N) on list fields generates maxItems in JSON Schema (Pydantic v2 behavior)"
    - "Field(max_length=N) on str fields generates maxLength in JSON Schema"
    - "Discriminated union on 'type' literal field for ContentBlock variants"
    - "Cardinality constraints derived from LayoutAnalyzer.SIZE_MODEL and USABLE_HEIGHT=575"

key-files:
  created:
    - pf/llm_schemas.py
    - tests/test_llm_schemas.py
  modified: []

key-decisions:
  - "Field(max_length=N) on list fields chosen over deprecated conlist() — Pydantic v2 idiomatic and generates correct maxItems in JSON Schema"
  - "Discriminated union (ContentBlock) on 'type' literal provides clean oneOf/discriminator in JSON Schema for LLM structured output"
  - "Constraints derived from SIZE_MODEL rather than hard-coded — values trace back to LayoutAnalyzer so they stay in sync conceptually"
  - "get_all_schemas() returns a copy of the registry dict to prevent caller mutation"

patterns-established:
  - "Layout model pattern: layout: Literal['name'] = 'name' as frozen default for instructor response_model usage"
  - "Optional list fields use anyOf wrapping in JSON Schema — tests handle both direct and anyOf array variants"

requirements-completed:
  - LLM-01

duration: 3min
completed: 2026-03-06
---

# Phase 3 Plan 01: LLM Schemas Summary

**Pydantic v2 per-layout models with JSON Schema maxItems/maxLength constraints for all 11 layouts, enabling overflow-safe LLM structured output via instructor**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-03-06T20:21:39Z
- **Completed:** 2026-03-06T20:24:32Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Created `pf/llm_schemas.py` with 11 layout Pydantic models (TitleSlide, TwoColumnSlide, ThreeColumnSlide, DataTableSlide, StatGridSlide, ChartSlide, ClosingSlide, ImageSlide, SectionSlide, QuoteSlide, TimelineSlide)
- Constraints derived from `LayoutAnalyzer.SIZE_MODEL` and `USABLE_HEIGHT=575` — list fields use `Field(max_length=N)` to produce `maxItems` in JSON Schema, string fields use `Field(max_length=N)` for `maxLength`
- Built `ContentBlock` discriminated union covering 7 block types (card, solution-box, stat-grid, table, dist-bars, val-bars, insight) with discriminator on `type` literal
- Added `PresentationOutput` wrapper with `yaml_config` str and `metrics` dict for the generation pipeline
- Created `get_layout_schema()` and `get_all_schemas()` registry functions for instructor/MCP integration
- 61 tests pass — parametrized coverage of all 11 layouts plus spot-checks on specific constraint values

## Task Commits

Each task was committed atomically:

1. **Task 1: Create pf/llm_schemas.py with per-layout Pydantic models** - `abaf474` (feat)
2. **Task 2: Write comprehensive tests for llm_schemas** - `9f08fb6` (test)

## Files Created/Modified

- `pf/llm_schemas.py` - 11 layout Pydantic models, block models, ContentBlock union, PresentationOutput, get_layout_schema/get_all_schemas registry
- `tests/test_llm_schemas.py` - 61 tests across 10 test classes; parametrized constraint checks, registry lookups, JSON Schema validation

## Decisions Made

- `Field(max_length=N)` on list fields chosen over deprecated `conlist()` — Pydantic v2 idiomatic and generates correct `maxItems` in JSON Schema output
- Discriminated union on `"type"` literal field (not string enum) — produces clean `oneOf` + `discriminator` in JSON Schema that instructor/OpenAI structured output handles correctly
- Constraint values derived from `SIZE_MODEL` (e.g., card bullets=4 → 60+4×22=148px vs USABLE_HEIGHT=575) so limits trace back to LayoutAnalyzer
- `get_all_schemas()` returns a copy of the registry dict to prevent accidental caller mutation

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `pf/llm_schemas.py` is ready as `response_model` for Plan 03-02 (instructor integration)
- `get_layout_schema()` is ready for Plan 03-03 (MCP `get_layout_schema` tool)
- All 11 layout models export named symbols matching the `exports` list in the plan frontmatter

## Self-Check: PASSED

- `pf/llm_schemas.py`: FOUND
- `tests/test_llm_schemas.py`: FOUND
- Commit `abaf474`: FOUND
- Commit `9f08fb6`: FOUND
- 61 tests: all passed

---
*Phase: 03-llm-integration*
*Completed: 2026-03-06*
