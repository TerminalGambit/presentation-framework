# Project Research Summary

**Project:** presentation-framework v0.3 Visual Editor
**Domain:** Next.js visual editor layered over a Python YAML-to-HTML slide deck build engine
**Researched:** 2026-03-08 (visual editor additions); 2026-03-05 (engine expansion baseline)
**Confidence:** HIGH (existing codebase inspected directly; stack verified via official docs and npm; features cross-validated against Slidev, Marp, Gamma, Beautiful.ai, Pitch; architecture derived from live code analysis)

---

## Executive Summary

The presentation-framework v0.3 milestone adds a browser-based visual editor to a production-complete Python build engine. The engine (YAML + JSON to Jinja2 to HTML) shipped a solid v0.2.0 baseline and does not change. The v0.3 work is a GUI layer that lets non-CLI users create and manage decks without writing YAML by hand. Research across all four domains converges on a single critical architectural constraint: the editor must never re-implement slide rendering. The Python Jinja2 output is the source of truth, and any attempt to mirror slide layouts in React will immediately diverge and produce fidelity bugs that are impossible to maintain. The entire preview strategy must use an iframe embedding the real Python-built HTML.

The recommended stack is Next.js 16 (App Router, TypeScript, Tailwind v4) for the editor frontend, with Zustand 5 for state management, CodeMirror 6 for YAML/JSON editing, and dnd-kit for slide reordering. The existing FastAPI platform already has all the endpoints the editor needs — no new Python packages are required. The backend integration uses Next.js rewrites to proxy to FastAPI, eliminating CORS complexity. For v0.3, the editor runs as a local dev server launched via a new `pf editor` CLI command. Packaging as a distributable app (Tauri v2) is explicitly deferred to a future milestone.

The highest risks are two state synchronization problems and one infrastructure constraint: (1) keeping the YAML code editor and visual form editor in sync must use a single Zustand store as the source of truth, with one serialization module as the only path between raw YAML and parsed state — never `useEffect` chains; (2) the existing `/api/build` rate limit of 10 requests/minute is incompatible with live preview editing cadence and must be raised before Phase 2 ships; (3) relative asset paths in the build output must be abstracted before any hosted/CDN serving is attempted. All three have clear, bounded mitigations and do not require architectural rethinking.

---

## Key Findings

### Recommended Stack

The editor is a separate `editor/` Node.js project at the repo root, not a Python module. The existing Python backend (`pf_platform/`) requires no new packages and no changes to existing endpoints for the editor to function. Three new FastAPI routes (`GET/PUT /api/projects/*`) handle local file read/write; one small change to `present.html.j2` adds a `postMessage` listener for slide navigation.

**Core technologies:**
- **Next.js 16 (App Router) + React 19 + TypeScript 5**: Editor framework — LTS stable since October 2025; Turbopack default; App Router server/client model maps cleanly to this editor's shell-renders-server, canvas-runs-client pattern. Do not use Next.js 15.x or Pages Router.
- **Zustand 5**: Editor global state — 3KB, no Provider wrapper, selector-based subscriptions, works cleanly with App Router server/client boundaries. Replaces Redux Toolkit (excessive ceremony) and React Context (no selector support = full-tree re-renders).
- **@uiw/react-codemirror + @codemirror/lang-yaml + @codemirror/lang-json**: YAML and JSON editing — 300KB total vs Monaco's 2.4MB; CodeMirror 6 modular extensions, React 19 compatible. Do not use Monaco Editor for this use case.
- **@dnd-kit/core + @dnd-kit/sortable**: Slide panel drag-to-reorder — accessible, grid-capable, actively maintained. Do not use react-beautiful-dnd (officially deprecated by Atlassian).
- **react-resizable-panels**: Three-pane editor layout — 8KB, `onLayout` persistence to localStorage, keyboard support.
- **Tailwind CSS 4 + shadcn/ui**: Editor UI chrome — Next.js 16 ships Tailwind v4 integration out of the box; shadcn/ui components are copied into the project (no external library dependency), built on Radix UI primitives.
- **FastAPI (existing, unchanged for core routes)**: All required `/api/build`, `/api/validate`, `/api/decks/*`, and `/ws/{deck_id}` endpoints already present; CORS already configured.

**Explicitly ruled out:** Monaco Editor (2.4MB bundle), react-beautiful-dnd (deprecated), Redux Toolkit (overhead), Electron (wrong deployment model for developer tool users), Next.js Pages Router (maintenance mode), tRPC (Python backend means no shared TypeScript types), SWR/React Query for build calls (imperative mutations, not subscriptions).

### Expected Features

Research surveyed Slidev, Marp, Gamma, Beautiful.ai, Pitch, and Slides.com. The primary user persona is non-technical users (marketers, PMs, consultants) who cannot write YAML. Developers and power users are a secondary persona served by the YAML escape hatch.

**Must have (table stakes):**
- Live slide preview in editor — core value proposition; users abandon if preview lags; must use iframe embedding real Python-built HTML
- Presentation management dashboard — "My presentations" grid for multi-deck workflows
- Template gallery with categories — non-developers always start from templates, not blank YAML
- Add / delete / duplicate / reorder slides — basic editing muscle memory
- Export from editor (HTML, PDF, PPTX) — every editor has download
- Autosave with status indicator — prevents anxiety about lost work
- Undo/redo (Ctrl+Z/Y) — universal expectation; highest-complexity table-stakes feature
- Error display for build failures — YAML invalidity must surface in UI, not silently fail

**Should have (competitive differentiation):**
- Side-by-side YAML editor + live preview — developer "escape hatch"; unique value of code-based tools
- Build overflow warnings as slide thumbnail badges — unique to this engine; no competitor offers this
- WCAG contrast warnings in UI — unique to this engine
- JSON metrics editor companion pane — power user feature; referenced paths surfaced visually
- Form-based slide editing per layout — structured fields generate valid YAML without exposing syntax
- Layout picker (visual grid of 16 layouts) — required when adding slides

**Defer to v2+:**
- Full WYSIWYG drag-and-drop element positioning — destroys code-as-configuration model
- Real-time collaborative editing — OT on YAML is non-trivial; WebSocket presenter sync already exists for viewing
- Built-in AI content writing — MCP tools handle the agent path; in-editor LLM is unbounded scope
- Git integration / version history — "export as YAML" gives users git-ready files they manage themselves
- Custom slide dimensions — fixed 1280x720 is a core engine constraint; not negotiable in v0.3

**Critical blocker (must fix in Phase 2):** The existing `/api/build` rate limit is 10 requests/minute. A debounced live preview at one build per 1.5 seconds would hit 40 builds/minute. The rate limit must be raised or removed for local editor mode before Phase 2 ships. This is not optional — without it, the live preview UX cannot be delivered.

### Architecture Approach

The system is three-tier: Next.js editor frontend communicates via Route Handler proxies to the existing FastAPI Python backend, which drives the unchanged PresentationBuilder core. The editor never calls FastAPI directly from the browser — all calls go through `lib/api.ts` to Next.js Route Handlers at `app/api/*`. Built slide HTML is served via `next.config.ts` rewrites (zero-latency, no Route Handler hop). The preview pane is an `<iframe>` embedding `present.html` with `postMessage` for slide navigation.

State is managed in three Zustand stores split by concern (editor, build, project). A single `lib/yaml-utils.ts` module handles bidirectional serialization between parsed `slides[]` and raw `rawYaml` — no `useEffect` chains. Forms write to the store via `updateSlide()` which re-serializes to `rawYaml`. YAML edits call `setRawYaml()` which parses into `slides[]`. These are the only two state mutation paths.

**Major components:**
1. **Next.js editor app** (`editor/`) — dashboard, template gallery, slide editor pages, Route Handler API proxies
2. **Zustand stores** — `editor-store` (slides, rawYaml, active slide, dirty flag), `build-store` (deckId, warnings, status), `project-store` (project list, current project)
3. **PreviewPane** — iframe embedding `present.html`, postMessage navigation control; never renders slides in React
4. **YamlEditor / MetricsEditor** — CodeMirror 6 wrappers for YAML and JSON; schema validation from `pf/schema.json`
5. **SlideForm** — per-layout form fields that generate YAML (form-to-YAML one direction only)
6. **FastAPI platform** — unchanged for all existing routes; gains `GET/PUT /api/projects/*` file-access routes for local mode
7. **pf CLI** — gains `pf editor` subcommand (20 lines of `subprocess.Popen` to start both servers + open browser)

The only modifications to existing Python code: (1) add `window.addEventListener('message')` to `present.html.j2` (~10 lines), (2) add `GET/PUT /api/projects/*` routes to `pf_platform/api.py`, (3) add `pf editor` command to `pf/cli.py`.

Build layer ordering: Infrastructure (Next.js scaffold + Route Handlers + rewrites) → Preview pane → YAML editor + stores + build hook → Dashboard + file I/O → Visual slide editor → Template gallery + export.

### Critical Pitfalls

1. **Preview fidelity divergence (day-one architecture decision)** — Building React components that render slide layouts produces two rendering engines that diverge immediately and permanently. Typography, CSS Grid math, chart rendering, and KaTeX all differ from the Python Jinja2 output. Use iframe embedding the real built HTML. Scale the 1280x720 canvas via `transform: scale(panelWidth / 1280)`. This must be the architecture decision on day one — retrofitting after building React layout components requires a partial rewrite.

2. **Two sources of truth for slide state** — YAML code editor and visual form editor cannot both be authoritative. Single Zustand store is the source of truth. All mutations go through `updateSlide()` (re-serializes to rawYaml) or `setRawYaml()` (parses to slides[]). Never sync via `useEffect`. No component should update both `rawYaml` and `slides[]` independently.

3. **Rate limit blocking live preview** — The existing 10/minute rate limit on `/api/build` is incompatible with editing cadence. Fix before Phase 2 ships or the editor's core value proposition cannot be delivered.

4. **Mermaid async export race condition** — Mermaid.js renders after `networkidle`, so Playwright captures the `<pre>` placeholder in PDF/PPTX exports. Fix: `document.body.dataset.pfReady = 'true'` sentinel after Mermaid resolves; `page.wait_for_function()` in `pdf.py`/`pptx.py`. Must be solved before Mermaid ships.

5. **Hosted platform relative asset paths** — All built HTML uses relative paths (`theme/variables.css`, `slide_NN.html`) that break when served from a CDN. Fix: `--base-url` build option or asset manifest before any upload feature. Plan this at end of v0.3 / start of v1.0.

6. **Schema tightening breaks existing decks** — When per-layout JSON schemas are introduced for LLM structured output, use `additionalProperties: true` and keep strict validation opt-in behind `--strict`. Existing v0.2 YAML files must continue building. Address at start of v0.4 before per-layout schemas are written.

---

## Implications for Roadmap

Research supports a layered build strategy where each phase delivers a working increment that validates assumptions before the next phase adds complexity. The feature research MVP definition maps directly to a three-phase editor build, followed by hardening phases aligned with the original v0.3-v1.0 engine expansion roadmap.

### Phase 1: Editor Infrastructure + Dashboard + Template Gallery

**Rationale:** The largest barrier for the target user (non-technical) is "I don't know YAML." Templates solve this without requiring the full editor. Building infrastructure and template gallery first validates that the user persona exists before investing in the complex YAML editor. API contracts defined first mean all subsequent UI is built on stable interfaces.

**Delivers:** Working browser app where users browse templates, fill a guided form, and export a PDF/PPTX with zero YAML exposure. Also establishes: Next.js scaffolding, API proxy layer, Zustand stores, FastAPI file-access routes (`/api/projects/*`), `pf editor` CLI command, postMessage listener in `present.html.j2`.

**Addresses from FEATURES.md:** Project dashboard, template gallery with categories, template content forms, export from gallery

**Avoids from PITFALLS.md:** Preview fidelity divergence (iframe-first architecture decided here before any React layout components are written); state management single-source-of-truth established before complexity is added

**Research flag:** SKIP — Next.js App Router scaffold, rewrites proxy, Zustand setup, static template manifest are all official-docs-level patterns. No research phase needed.

### Phase 2: Live YAML Editor + Slide Management

**Rationale:** Power users and developers want raw YAML access. This phase makes the editor a viable CLI replacement for iterative editing. The rate limit fix is a hard dependency — must be resolved before this phase ships. YAML editor before form editor because the form editor is a layer on top of the YAML state model and requires a tested serialization pipeline first.

**Delivers:** Split-pane CodeMirror YAML editor + live iframe preview, slide thumbnail panel with drag-to-reorder, autosave, undo/redo, build warnings surfaced in UI, JSON metrics editor, export from editor toolbar.

**Addresses from FEATURES.md:** YAML + live preview (P1), slide thumbnail panel (P1), autosave (P1), export (P1), drag-to-reorder (P2), build warnings (P2), undo/redo (P2), JSON metrics editor (P2)

**Avoids from PITFALLS.md:** Rate limit blocker (fix before this phase ships), state two-source-of-truth (single `yaml-utils.ts` established here), `useEffect` sync anti-pattern, `deckId` in URL causing history pollution (deckId lives in `build-store`, not URL)

**Uses from STACK.md:** @uiw/react-codemirror, @codemirror/lang-yaml, @codemirror/lang-json, @dnd-kit/sortable, react-resizable-panels, Zustand with Immer middleware, js-yaml for client-side YAML parsing

**Research flag:** NEEDS research on two items before planning: (1) undo/redo YAML snapshot stack design — memory cap, interaction with form mode edits, maximum history depth trade-offs; (2) CodeMirror 6 controlled-value pattern performance with large YAML files (500+ lines) — whether the `value` prop approach causes input lag that warrants uncontrolled mode with `initialDoc`.

### Phase 3: Visual Form Editor

**Rationale:** The most complex phase. Form-to-YAML state management requires typed form definitions for all 16 layouts. The bidirectional sync problem is the hardest engineering problem in the editor. Only worth building once Phases 1 and 2 confirm the user base and usage patterns — this is a significant investment to make before validating demand.

**Delivers:** Form-based slide editing with per-layout field UI (no YAML syntax exposure), layout picker (visual grid of 16 layouts when adding a slide), theme controls UI (color pickers, font selector, style preset), speaker notes input, slide transitions picker.

**Addresses from FEATURES.md:** Form-based slide editing (P2), layout picker (P2), theme controls UI (P2), speaker notes (P3), transitions (P3)

**Avoids from PITFALLS.md:** Form-YAML sync explosion (one-directional: forms generate YAML; YAML is never parsed back to form state; conflict mode is either form mode or YAML mode, not both simultaneously); YAML comment loss documented as known limitation upfront

**Research flag:** NEEDS research before planning: (1) Per-layout form schema design — choose between generating forms from `pf/schema.json` (single source of truth, complex) vs hand-authored form definitions per layout (simpler, duplicated); (2) YAML comment preservation — `js-yaml` drops comments on round-trip; assess whether `yaml` package with CST API is worth the complexity for the target user persona.

### Phase 4: Rich Media + Export Hardening

**Rationale:** Covers the v0.3 rich media engine work (Mermaid, code highlighting, map layout, video embed) and ensures all async library render issues are solved before the export pipeline is expanded. The Playwright race condition must be fixed here. The `--base-url` path abstraction needed for hosted mode also lands at the end of this phase.

**Delivers:** Mermaid.js diagram support with `data-pf-ready` sentinel, code syntax highlighting (Highlight.js), Google Maps embed layout, video embed layout, editable PPTX native renderer expansion, Playwright single-context browser pool refactor, `--base-url` build option for CDN-safe output.

**Addresses from FEATURES.md:** Code highlighting (P1 missed from v0.2), Mermaid diagrams (P1), video embed (P1), editable PPTX completion (P2)

**Avoids from PITFALLS.md:** Mermaid async export race condition (sentinel pattern), Playwright per-slide browser spawn (single-context refactor in `_render_image_fallback()`), external font download for offline export, hosted platform relative path breakage (`--base-url` fix)

**Research flag:** SKIP for Mermaid sentinel and Playwright refactor (well-documented patterns). NEEDS brief research on Google Maps API key handling for hosted mode — Static API vs Embed API security model (API key must not appear in output HTML).

### Phase 5: Plugin Ecosystem + Platform Hardening (v0.4–v1.0)

**Rationale:** Plugin architecture is a prerequisite for the LLM layer (list_layouts and get_layout_schema must be plugin-aware). Platform requires plugin stability (hosted builds must match local builds). Schema isolation decisions made here cannot be easily reversed. The `autoescape` XSS hardening must happen before `generate_presentation` processes untrusted LLM output.

**Delivers:** `pf/registry.py` (entry point + directory plugin discovery), per-layout LLM generation schemas with `maxItems` constraints (`pf/llm_schemas.py`), content density optimizer (`pf/optimizer.py`), new MCP tools (`generate_from_prompt`, `optimize_slide`, `suggest_layout`), FastAPI platform service (`pf_platform/` expansion), Jinja2 autoescape hardening for LLM input paths, API rate limiting for hosted REST API.

**Addresses from FEATURES.md:** Plugin layout system, generate_presentation MCP tool, hosted web viewer, embed codes, REST API

**Avoids from PITFALLS.md:** Schema tightening backward compatibility (`additionalProperties: true`, strict mode opt-in), plugin CSS isolation (scoped to slides that use the layout), LLM overloaded slides (separate LLM schemas with `maxItems`), autoescape XSS, hosted API rate limiting

**Research flag:** NEEDS research for data source plugin credential management (OAuth2 for Google Sheets in a CLI context — keychain vs env vars vs config file pattern). Multi-agent workflow contracts and suggest_layout heuristics may also benefit from phase research.

### Phase Ordering Rationale

- Infrastructure before UI because API contracts must be stable before UI is built on top; rework cost is lowest if contracts are defined first
- Template gallery before YAML editor because it validates the non-developer user persona cheaply before investing in the complex code editor
- YAML editor before form editor because forms are a layer on top of the YAML state model; testing the serialization path first ensures forms can be verified against a known-good pipeline
- Rich media after both editor phases because export hardening work (Playwright, Mermaid sentinel) benefits from having real editor-triggered builds to test against end-to-end
- Plugin ecosystem before LLM integration because LLM tools must describe plugin layouts; building LLM schemas before the registry forces a rewrite the moment plugins exist
- Platform last because it requires plugin stability (consistent build output) and the `--base-url` path abstraction

### Research Flags

**Needs deeper research before planning:**
- Phase 2: Undo/redo YAML snapshot stack design — memory cap, interaction with form mode
- Phase 2: CodeMirror 6 controlled-value performance with large YAML files
- Phase 3: Per-layout form schema design strategy (derived vs hand-authored)
- Phase 3: YAML comment preservation options and trade-offs
- Phase 4: Google Maps API key security model for hosted mode
- Phase 5: Data source plugin credential management (OAuth2 in CLI context)

**Standard patterns (skip research-phase):**
- Phase 1: Next.js App Router scaffold, rewrites proxy, Zustand setup, static template manifest
- Phase 4: Mermaid `data-pf-ready` sentinel, Playwright single-context browser pool
- Phase 5 (platform layer): FastAPI + SQLAlchemy 2.x + S3 storage adapter — standard Python web platform patterns

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | MEDIUM-HIGH | Next.js 16 and React 19 verified via official release blogs (October 2025); npm package versions spot-checked. Next.js 16 is recent enough that some edge cases may not have community solutions yet. Spot-check npm packages before scaffolding. |
| Features | HIGH | Cross-validated against 6 competitor tools. Rate limit issue is a concrete, measured constraint from live codebase. MVP definition is well-grounded in competitor UX research. |
| Architecture | HIGH | Primary sources are direct codebase inspection and official Next.js 16 docs. Build latency estimates from existing system behavior. Integration patterns from live `pf_platform/api.py` code. |
| Pitfalls | HIGH | Pitfalls derived from direct codebase analysis, not generic advice. Mermaid race condition, Playwright browser spawn, rate limit, schema tightening, and relative path issues all confirmed against actual code. |

**Overall confidence:** HIGH

### Gaps to Address

- **Rate limit design:** Remove entirely for local `pf editor` mode (single user, no abuse vector); keep for hosted REST API with per-token limits. Decision needed at Phase 2 planning.
- **YAML comment preservation:** `js-yaml` drops comments on round-trip. Document this as a known limitation for Phase 2 (YAML editor round-trips via store don't preserve comments), and revisit at Phase 3 planning (form editor has the same issue). The `yaml` package with CST API preserves comments but adds complexity.
- **Template library scope:** Research assumes templates are static YAML files checked into the repo. No decision on count, categories, or maintenance ownership. This is a content gap, not a technical gap — decide at Phase 1 planning.
- **Tauri v2 packaging (future):** Deferred to v0.4+. Research confirms the `dieharders/example-tauri-v2-python-server-sidecar` pattern works, but Rust toolchain and Python binary bundling have not been tested in this repo.

---

## Sources

### Primary (HIGH confidence)
- `pf_platform/api.py` — existing endpoints, CORS config, rate limits; direct codebase read
- `pf/builder.py`, `pf/analyzer.py`, `pf/pdf.py`, `pf/pptx_native.py` — build pipeline behavior; direct codebase read
- `templates/present.html.j2`, `pf/schema.json` — output format and validation schema; direct codebase read
- [Next.js rewrites/proxy docs](https://nextjs.org/docs/app/getting-started/proxy) — rewrite configuration pattern for FastAPI proxy
- [Next.js BFF pattern](https://nextjs.org/docs/app/guides/backend-for-frontend) — Route Handler as API proxy
- [shadcn/ui Tailwind v4 docs](https://ui.shadcn.com/docs/tailwind-v4) — Tailwind v4 compatibility confirmed
- [Sourcegraph: Monaco to CodeMirror migration](https://sourcegraph.com/blog/migrating-monaco-codemirror) — 43% JS size reduction (measured data)
- [Tauri v2 Next.js guide](https://v2.tauri.app/start/frontend/nextjs/) — future packaging reference

### Secondary (MEDIUM confidence)
- [Next.js 16 release blog](https://nextjs.org/blog/next-16) — Turbopack default, React Compiler stable, LTS status; web search verified March 2026
- [Zustand npm](https://www.npmjs.com/package/zustand) — v5.0.11; React 19 compatible
- [@uiw/react-codemirror GitHub](https://github.com/uiwjs/react-codemirror) — React 19 compatibility confirmed v4.25+
- [dnd-kit docs](https://dndkit.com/) — sortable preset, accessibility model
- [Slidev UI Guide](https://sli.dev/guide/ui) — side editor pattern; presenter mode
- [Gamma creation flow](https://help.gamma.app/en/articles/7838093) — template-first onboarding UX research
- [Beautiful.ai Smart Slides](https://www.beautiful.ai/smart-slides) — form-based editing model research
- [dieharders/example-tauri-v2-python-server-sidecar](https://github.com/dieharders/example-tauri-v2-python-server-sidecar) — Tauri + FastAPI sidecar community example
- PyPI package versions — instructor, pydantic, fastapi, uvicorn, sqlalchemy, alembic, anthropic, openai; verified via pip index

### Tertiary (LOW confidence)
- [Puck: Top 5 DnD Libraries 2026](https://puckeditor.com/blog/top-5-drag-and-drop-libraries-for-react) — dnd-kit as current standard (vendor blog; corroborated by npm download data)
- Competitor feature analysis (Gamma, Beautiful.ai, Pitch) — web search March 2026; some feature sets move fast, re-verify at implementation time

---

*Research completed: 2026-03-08*
*Ready for roadmap: yes*
