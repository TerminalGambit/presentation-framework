# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v0.2 — v1.0 Feature Complete

**Shipped:** 2026-03-07
**Phases:** 4 | **Plans:** 21 | **Commits:** 74

### What Was Built
- 5 new rich media layouts (code, mermaid, video, map, toc) with CDN auto-detection and async export support
- Native PPTX renderers expanded from 0 to 10/11 layouts with editable text shapes
- Full plugin ecosystem — layout, theme, and data source plugins with entry point discovery, CSS isolation, and CLI
- LLM integration layer — Pydantic v2 schemas per layout, content density optimizer, 5 new MCP tools
- XSS sanitization pipeline (bleach + regex fallback) for LLM-generated content
- Accessibility checker with ARIA labels, alt text, and high-contrast mode
- FastAPI hosted platform with shareable URLs, iframe embedding, SQLite analytics, and WebSocket sync
- `--base-url` support for CDN/hosted asset paths

### What Worked
- **Concentric ring architecture** — each phase built on the previous without touching PresentationBuilder core; clean separation of concerns
- **Parallel phase execution** — Phases 2-4 were planned and executed with minimal cross-phase friction; phases could be developed somewhat independently
- **data-pf-ready sentinel pattern** — solved the async content export problem once in Phase 1 and it carried through all subsequent exports
- **gsd-tools automation** — tooling for phase execution, verification, and state management kept the process consistent across 21 plans
- **Test coverage** — starting at 57 tests and ending at 482; every plan added tests, catching regressions early

### What Was Inefficient
- **SUMMARY frontmatter gaps** — 4 SUMMARY.md files forgot to list requirements_completed; caught only at milestone audit
- **Phase 2 roadmap checkbox** — ROADMAP.md showed Phase 2 as `[ ]` (incomplete) despite all 5 plans having SUMMARYs; the checkbox tracking was inconsistent with the actual state
- **Beacon/sync script injection** — Plans 04-03 and 04-04 created the infrastructure (SQLite store, WebSocket manager) and the JS scripts as constants but deferred the injection into served HTML; this created an integration gap discovered only during milestone audit
- **LLM schema coverage** — Phase 3 schemas covered the original 11 layouts but didn't account for the 5 new layouts from Phase 1; cross-phase schema synchronization was missed

### Patterns Established
- **CDN auto-detection** — `_scan_features()` scans all slide layouts and block types to conditionally inject CDN scripts; extensible pattern for future dependencies
- **Plugin CSS isolation** — `.pf-layout-{name}` class prefix convention for scoped CSS without build tools
- **Lazy imports in MCP tools** — `import instructor` inside function body so optional dependencies don't crash the server
- **Parse-sanitize-reserialize for YAML** — safer than string-level manipulation for XSS hardening
- **Sentinel-gated export** — `data-pf-ready` attribute + `wait_for_selector` for all async content

### Key Lessons
1. **Cross-phase integration needs explicit verification** — individual phase verifications can pass while E2E flows remain broken; the integration checker caught issues that 4 passing VERIFICATIONs missed
2. **Schema registries need to be updated when new layouts are added** — adding a layout in one phase should trigger a schema update in the LLM layer; consider a shared layout registry that feeds both templates and schemas
3. **Script injection should happen at build-time, not exist as orphaned constants** — BEACON_SCRIPT and SYNC_SCRIPT should be injected by `run_build()` post-processing, not left as documentation constants

### Cost Observations
- Model mix: ~20% opus (planning/verification), ~70% sonnet (execution), ~10% haiku (quick searches)
- Sessions: ~15-20 across 7 days
- Notable: Parallel plan execution within phases significantly reduced calendar time; 21 plans in 7 days

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Commits | Phases | Key Change |
|-----------|---------|--------|------------|
| v0.2 | 74 | 4 | First full milestone with gsd tooling; established verification + audit pattern |

### Cumulative Quality

| Milestone | Tests | LOC (Python) | Layouts |
|-----------|-------|--------------|---------|
| v0.2 | 482 | 11,528 | 16 (11 original + 5 new) |

### Top Lessons (Verified Across Milestones)

1. Cross-phase integration gaps are invisible to per-phase verification — always run milestone audit before shipping
2. Schema/registry synchronization across phases requires explicit tracking
