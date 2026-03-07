---
phase: 03-llm-integration
plan: "03"
subsystem: api
tags: [mcp, instructor, xss-sanitization, bleach, llm, generate-presentation]

requires:
  - phase: 03-llm-integration
    plan: "01"
    provides: PresentationOutput, get_layout_schema registry for instructor response_model

provides:
  - "pf/sanitize.py: safe_llm_text() and sanitize_slide_data() XSS hardening utilities"
  - "pf/mcp_server.py: generate_presentation MCP tool backed by instructor + lazy import"
  - "pf/mcp_server.py: get_layout_schema MCP tool exposes JSON Schema per layout"
  - "setup.py: pf[llm] optional dependency group (instructor[anthropic]>=1.13.0, bleach>=6.0)"
  - "22 new tests: XSS sanitization coverage + generate_presentation + get_layout_schema"

affects:
  - "03-04: generate_presentation tool is now the LLM generation entry point for agents"
  - "templates: LLM content sanitized before reaching autoescape=False Jinja2 env"

tech-stack:
  added: [bleach>=6.0, instructor[anthropic]>=1.13.0 (optional via pf[llm])]
  patterns:
    - "Lazy import inside MCP tool function — graceful ImportError message when extra not installed"
    - "sanitize yaml_config by parsing to dict, cleaning per-slide data, re-serializing to YAML"
    - "sanitize_slide_data() recurses dicts+lists, applies safe_llm_text() to all string values"
    - "bleach.clean() primary sanitizer; regex fallback strips dangerous tags when bleach absent"

key-files:
  created:
    - pf/sanitize.py
  modified:
    - pf/mcp_server.py
    - setup.py
    - tests/test_builder.py
    - tests/test_mcp_server.py

key-decisions:
  - "Sanitize yaml_config by parse-sanitize-reserialize (not string-level) — avoids partial YAML corruption from regex on serialized strings"
  - "bleach.clean() with ALLOWED_TAGS list chosen over full HTML stripping — preserves formatting (b, em, code) while blocking XSS vectors"
  - "Regex fallback strips dangerous element pairs first, then orphan opening/closing tags — handles malformed HTML without bleach"
  - "GENERATE_SYSTEM_PROMPT defined as module-level constant — readable, testable, and reusable if prompt needs iteration"
  - "sanitize_slide_data() accepts dict|list|str|scalar — single function for both slide data dicts and metrics dicts"

patterns-established:
  - "LLM sanitization pipeline: PresentationOutput.yaml_config -> yaml.safe_load -> per-slide sanitize_slide_data -> yaml.dump"
  - "generate_presentation always returns a dict: {yaml_config, metrics} on success or {error} on failure"

requirements-completed:
  - LLM-02
  - LLM-07

duration: ~4min
completed: 2026-03-06
---

# Phase 3 Plan 03: MCP generate_presentation Tool + XSS Sanitization Summary

**generate_presentation MCP tool backed by instructor with lazy import, pf/sanitize.py XSS hardening via bleach (with regex fallback), pf[llm] optional extra, and 22 new tests covering sanitization and MCP tool behavior**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-03-06T20:27:08Z
- **Completed:** 2026-03-06T20:30:44Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Created `pf/sanitize.py` with `safe_llm_text()` (bleach-backed HTML sanitizer with regex fallback), `sanitize_slide_data()` (recursive dict/list walker), `ALLOWED_TAGS` and `ALLOWED_ATTRS` constants
- Added `generate_presentation` MCP tool to `pf/mcp_server.py`: lazy-imports `instructor`, returns graceful error when `pf[llm]` not installed, calls LLM via `instructor.from_provider()`, sanitizes both yaml_config (parse-sanitize-reserialize pipeline) and metrics dict
- Added `get_layout_schema` MCP tool to `pf/mcp_server.py`: exposes Pydantic-generated JSON Schema for any layout name via `pf.llm_schemas.get_layout_schema()`
- Updated `setup.py` with `pf[llm]` optional extra: `instructor[anthropic]>=1.13.0` and `bleach>=6.0`
- Added 22 new tests: 11 in `test_builder.py` (sanitize module coverage including no-mutation guarantee, scalar passthrough, deeply nested structures) + 11 in `test_mcp_server.py` (generate_presentation: missing-dep error, mocked instructor with XSS assertion, metrics sanitization, exception handling; get_layout_schema: all 11 layouts, maxItems presence, timeline steps field)
- Full test suite: 433 tests pass (up from 411)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add pf[llm] extra, create pf/sanitize.py, and add generate_presentation MCP tool** - `ab53d3e` (feat)
2. **Task 2: Write tests for sanitization and generate_presentation** - `bb2e269` (test)

## Files Created/Modified

- `pf/sanitize.py` - safe_llm_text() with bleach+regex fallback, sanitize_slide_data() recursive walker, ALLOWED_TAGS/ALLOWED_ATTRS constants
- `pf/mcp_server.py` - generate_presentation tool (instructor lazy import, GENERATE_SYSTEM_PROMPT, sanitization pipeline) + get_layout_schema tool
- `setup.py` - pf[llm] optional extra added to extras_require
- `tests/test_builder.py` - TestSanitizeLLMContent (10 tests) + test_llm_content_escaping integration marker
- `tests/test_mcp_server.py` - TestGeneratePresentation (5 tests) + TestGetLayoutSchema (6 tests)

## Decisions Made

- Sanitize `yaml_config` by parsing to dict first (parse-sanitize-reserialize) rather than regex on the serialized YAML string — avoids partial YAML corruption and correctly targets only user-visible string values inside slide data dicts
- `bleach.clean()` with explicit `ALLOWED_TAGS` list chosen over blanket HTML stripping — preserves formatting markup (`<b>`, `<em>`, `<code>`) that agents legitimately produce while blocking all XSS vectors
- Regex fallback handles two cases: (1) paired dangerous elements like `<script>...</script>` via `_DANGEROUS_ELEMENT_RE`, (2) orphan opening/closing tags via separate patterns — robust against malformed LLM HTML output
- `GENERATE_SYSTEM_PROMPT` defined as module-level constant (not inline) — readable, writable without touching function body, and visible in tests when checking prompt content
- `sanitize_slide_data()` accepts `dict|list|str|scalar` instead of `dict` only — same function works for both slide `data` dicts and the top-level `metrics` dict without special casing

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

- `pip install 'pf[llm]'` installs `instructor[anthropic]>=1.13.0` and `bleach>=6.0`
- Without `pf[llm]`, `generate_presentation` returns `{"error": "LLM features require: pip install 'pf[llm]'"}` — graceful degradation, no crash

## Next Phase Readiness

- `generate_presentation` MCP tool is the LLM entry point for agents in subsequent plans
- `pf/sanitize.py` is importable by any builder code that processes LLM content
- `get_layout_schema` exposes constraint-bearing JSON Schemas to LLM agents for structured output

## Self-Check: PASSED

- `pf/sanitize.py`: FOUND
- `pf/mcp_server.py` (contains generate_presentation): FOUND
- `setup.py` (contains llm extra): FOUND
- `tests/test_builder.py` (contains test_llm_content_escaping): FOUND
- `tests/test_mcp_server.py` (contains TestGeneratePresentation): FOUND
- Commit `ab53d3e`: FOUND
- Commit `bb2e269`: FOUND
- 433 tests: all passed

---
*Phase: 03-llm-integration*
*Completed: 2026-03-06*
