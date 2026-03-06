# Roadmap: Presentation Framework

## Overview

Starting from a solid v0.2.0 baseline (11 layouts, MCP server, PDF/PPTX export), the path to v1.0 adds four concentric capability rings. Phase 1 closes the table-stakes developer credibility gaps — code highlighting and slide fragments — while finishing the export pipeline. Phase 2 opens the extension model so community contributors can add layouts, themes, and data sources. Phase 3 wires in LLM-native generation with cardinality-constrained schemas and a content density optimizer. Phase 4 wraps everything in a hosted service with shareable URLs, embed codes, and a REST API. Each ring is independently valuable and leaves the core `PresentationBuilder` untouched.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Rich Media + Export Polish** - Close developer credibility gaps (code highlighting, fragments, Mermaid, video, maps) and finish the export pipeline (all-layout PPTX, PDF notes, async sentinel, browser context fix) — gap closure in progress (EXPORT-02)
- [ ] **Phase 2: Plugin Ecosystem** - Open the extension model with layout, theme, and data source plugins discoverable via entry points and a `pf plugins` CLI
- [ ] **Phase 3: LLM Integration** - Add generation-constrained layout schemas, a content density optimizer, and `generate_presentation` MCP tool with XSS-hardened template rendering
- [ ] **Phase 4: Hosted Platform** - Ship a FastAPI service with shareable URLs, embed codes, REST API, analytics, and presenter WebSocket sync

## Phase Details

### Phase 1: Rich Media + Export Polish
**Goal**: Developers can embed code, diagrams, video, and maps in slides, and all export formats reliably render async content across all 11 layouts
**Depends on**: Nothing (first phase; builds on v0.2.0 baseline)
**Requirements**: MEDIA-01, MEDIA-02, MEDIA-03, MEDIA-04, MEDIA-05, MEDIA-06, MEDIA-07, EXPORT-01, EXPORT-02, EXPORT-03, EXPORT-04
**Success Criteria** (what must be TRUE):
  1. User can add a fenced code block to any slide and see language-aware syntax highlighting in the rendered HTML output
  2. User can mark bullet points or elements with `fragment: true` and have them reveal one-by-one during presentation using keyboard navigation
  3. User can define a Mermaid.js diagram in YAML and it renders correctly in both the HTML viewer and PDF/PPTX exports (no raw `<pre>` text in exports)
  4. User can embed a YouTube, Vimeo, or MP4 video with a thumbnail preview in HTML and a static frame in PDF/PPTX exports
  5. `pf pptx` produces fully editable native shapes (text, tables, bars) for all 11 layouts, not image screenshots
**Plans**: 7 plans

Plans:
- [x] 01-01-PLAN.md — Foundation infrastructure (schema, CDN auto-detect, sentinel, per-slide CSS, block dispatch stubs)
- [x] 01-02-PLAN.md — Code syntax highlighting (Highlight.js, code layout + block type)
- [x] 01-03-PLAN.md — Fragment reveal system (CSS + navigator JS state machine)
- [x] 01-04-PLAN.md — Mermaid diagrams, video embeds, interactive maps (3 layout + block types)
- [x] 01-05-PLAN.md — Auto-generated TOC slide + per-slide CSS tests
- [x] 01-06-PLAN.md — Export pipeline (sentinel waiting, native PPTX expansion, PDF notes, shared browser context)
- [ ] 01-07-PLAN.md — Gap closure: native PPTX renderers for data-table, image, timeline (closes EXPORT-02)

### Phase 2: Plugin Ecosystem
**Goal**: Developers can create, distribute, and install custom layout, theme, and data source plugins without modifying the core engine
**Depends on**: Phase 1
**Requirements**: PLUG-01, PLUG-02, PLUG-03, PLUG-04, PLUG-05, PLUG-06
**Success Criteria** (what must be TRUE):
  1. Developer can create a Python package with a `pf.layouts` entry point, run `pip install` it, and have the layout appear in `pf build` without any core code changes
  2. Developer can install a theme package (`pip install pf-theme-<name>`) and reference it by name in `presentation.yaml`
  3. Developer can create a data source plugin that fetches from a Google Sheet and passes values into metrics interpolation — credentials managed via environment variables or config file
  4. User can run `pf plugins list` to see installed plugins and `pf plugins install <name>` to install from a registry
  5. Plugin CSS is scoped to its layout's slides and does not affect slides using other layouts
**Plans**: TBD

Plans:
- [ ] 02-01: Plugin registry (`pf/registry.py`) with entry point discovery and directory scanning; backward-compatible builder injection
- [ ] 02-02: Layout plugin contract (template inheritance pattern, CSS scoping spec, schema isolation `additionalProperties: true`)
- [ ] 02-03: Theme plugin system (installable packages, theme discovery, override chain)
- [ ] 02-04: Data source plugins (Google Sheets, REST API, database adapters; credential management pattern)
- [ ] 02-05: `pf plugins` CLI command group (list, install, info); updated `list_layouts()` MCP tool to include plugin layouts

### Phase 3: LLM Integration
**Goal**: AI agents can reliably generate complete, correctly-sized presentations from a prompt, with overflowing slides automatically split and all template rendering hardened against injection
**Depends on**: Phase 2
**Requirements**: LLM-01, LLM-02, LLM-03, LLM-04, LLM-05, LLM-06, LLM-07
**Success Criteria** (what must be TRUE):
  1. Each layout's JSON Schema includes `maxItems` and `maxLength` constraints so an LLM calling `get_layout_schema()` cannot produce a slide that overflows
  2. Agent can call `generate_presentation(prompt, style, length)` via MCP and receive valid YAML + JSON that builds without overflow warnings on the first attempt
  3. Agent can call `optimize_slide(slide_yaml)` and receive a split into two slides when content exceeds the layout's density threshold
  4. Jinja2 templates use selective autoescaping for any rendering path that processes LLM-generated or API-submitted content, preventing XSS
  5. ARIA labels are present on all interactive slide elements and alt text is generated for images lacking it
**Plans**: TBD

Plans:
- [ ] 03-01: Layout LLM schemas (`pf/llm_schemas.py`) — per-layout Pydantic models with cardinality constraints, separate from `schema.json` validation schemas
- [ ] 03-02: Content density optimizer (`pf/optimizer.py`) — algorithmic slide splitter using existing `LayoutAnalyzer`
- [ ] 03-03: `generate_presentation` MCP tool — `instructor`-based structured output, `pf[llm]` optional dependency group, autoescape hardening
- [ ] 03-04: Slide suggestion + multi-agent workflow (suggest_layout MCP tool, documented multi-agent pattern: researcher → data → layout → review)
- [ ] 03-05: Accessibility pass (ARIA labels, alt text generation, high-contrast mode toggle)

### Phase 4: Hosted Platform
**Goal**: Users can share a presentation via URL, embed it in any webpage, hit a REST API to build programmatically, and see view analytics — with presenter WebSocket sync for live delivery
**Depends on**: Phase 3
**Requirements**: PLAT-01, PLAT-02, PLAT-03, PLAT-04, PLAT-05, PLAT-06
**Success Criteria** (what must be TRUE):
  1. User can upload a built deck and receive a shareable URL that shows the full slide navigator experience to anyone with the link
  2. User can copy an iframe snippet from the platform and paste it into Notion, a blog, or docs — the embedded deck navigates correctly
  3. REST API `POST /build` accepts `presentation.yaml` + `metrics.json` and returns a download URL for the built HTML deck
  4. Platform dashboard shows total views and per-slide engagement (time-on-slide) for each shared deck
  5. `pf build` accepts `--base-url <url>` so all asset paths in the output are absolute and work correctly when served from a CDN or the hosted platform
**Plans**: TBD

Plans:
- [ ] 04-01: `--base-url` path abstraction (rewrite asset paths in build output; prerequisite for all upload features)
- [ ] 04-02: FastAPI platform service (`platform/api.py`, `platform/worker.py`) with build job queue and file storage adapter (local fs → S3/R2)
- [ ] 04-03: Shareable URL viewer + embed codes (iframe snippet generator, public viewer route)
- [ ] 04-04: REST API endpoints (build, validate, generate) with rate limiting and OpenAPI docs
- [ ] 04-05: Analytics beacon + dashboard (per-slide view tracking, time-on-slide aggregation)
- [ ] 04-06: Presenter WebSocket sync (last-writer-wins slide position broadcast for live delivery)

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Rich Media + Export Polish | 6/7 | Gap closure in progress | - |
| 2. Plugin Ecosystem | 0/5 | Not started | - |
| 3. LLM Integration | 0/5 | Not started | - |
| 4. Hosted Platform | 0/6 | Not started | - |
