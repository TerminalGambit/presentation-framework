# Project Research Summary

**Project:** presentation-framework
**Domain:** Python presentation engine — rich media, plugin ecosystem, LLM integration, hosted platform
**Researched:** 2026-03-05
**Confidence:** HIGH (stack and pitfalls verified against codebase; features from codebase + training data; architecture from direct code analysis)

## Executive Summary

The presentation-framework is a YAML + JSON -> Jinja2 -> HTML slide deck generator that has shipped a solid v0.2.0 baseline. The roadmap through v1.0 adds four concentric capability rings: rich media (v0.3), plugin ecosystem (v0.4), LLM integration (v0.5), and a hosted platform (v1.0). Each ring is additive — no existing behavior needs to change to build the next layer. This is a genuine architectural strength: the core `PresentationBuilder` should remain untouched across all four expansion phases.

The recommended approach follows well-established Python patterns throughout. Rich media is pure template work — no new Python dependencies needed, just CDN-loaded JS libraries (Highlight.js, Mermaid.js, Leaflet) gated by `theme.*` feature flags. Plugin architecture uses Python's standard `importlib.metadata` entry points, the same mechanism as pytest and Sphinx. LLM integration uses `instructor` + Pydantic to produce typed structured output per slide layout, cleanly separating generation concerns from rendering. The platform layer wraps the existing build pipeline in a FastAPI service with a job queue and S3-compatible storage. Each component has clear boundaries and can be built and tested independently.

The most important risk to manage across all phases is the existing `autoescape=False` Jinja2 configuration, which is safe today (CLI users own their input) but becomes a critical XSS vulnerability the moment LLM-generated content or a hosted REST API reaches templates. This must be addressed in v0.5 before `generate_presentation` ships. The second most important risk is the Mermaid.js async export race condition: diagrams render correctly in the browser but not in Playwright PDF/PPTX exports unless a `data-pf-ready` sentinel is added. This must be solved in v0.3 before Mermaid ships. Both are well-understood, tractable fixes — they just must not be deferred.

## Key Findings

### Recommended Stack

The v0.2.0 baseline already contains all core Python dependencies. New capability layers add optional dependency groups via `pyproject.toml` extras. Rich media requires zero new Python packages — Highlight.js 11.x, Mermaid.js 11.x, and Leaflet 1.9.x are injected via Jinja2 templates only when the corresponding `theme.*` flag is set. The plugin architecture requires only `importlib.metadata` (stdlib) for the common case, with `pluggy 1.6.0` as an optional addition if hook complexity warrants it. LLM integration adds `instructor 1.14.5` + `pydantic 2.12.5` plus provider SDKs (`anthropic 0.84.0` / `openai 2.25.0`) as a `pf[llm]` optional group. The platform layer adds `fastapi 0.135.1` + `uvicorn 0.41.0` + `sqlalchemy 2.0.48` + `alembic 1.18.4` + `boto3 1.42.x` as `pf[platform]`.

**Core technologies for new capabilities:**
- Highlight.js 11.x: code syntax highlighting — zero-config auto-detection, CDN-only, no build step
- Mermaid.js 11.x: animated diagram rendering — ESM CDN, text-definition in `<pre class="mermaid">`, matches YAML-driven philosophy
- `importlib.metadata` entry_points: plugin discovery — stdlib, pip-native, same mechanism as pytest/Sphinx/Babel
- instructor 1.14.5: LLM structured output — wraps Anthropic/OpenAI/Gemini with Pydantic response models; returns typed instances, not raw JSON
- Pydantic 2.12.5: schema definition for LLM layout contracts — also required by FastAPI 0.135.x
- FastAPI 0.135.1: REST API for platform layer — async, Pydantic-native, auto-generates OpenAPI docs, shares Pydantic models with LLM layer
- SQLAlchemy 2.0.48 + Alembic 1.18.4: platform persistence — async-compatible, SQLite dev / PostgreSQL prod with no code changes

JS CDN library versions (Highlight.js, Mermaid.js, Leaflet) are from training data through Aug 2025 and should be verified against current CDN URLs before implementation.

### Expected Features

The v0.2.0 engine is missing two table-stakes developer features — code syntax highlighting and slide fragments — that every open-source competitor (reveal.js, Marp, Slidev) has shipped. These are the most urgent gaps and must close in v0.3 or developer credibility suffers. The engine already leads all open-source competitors on AI-agent features (structured data model, MCP server, idempotent builds).

**Must have (table stakes not yet shipped):**
- Code syntax highlighting — the single biggest credibility gap vs. reveal.js/Marp/Slidev; every demo deck has code
- Slide fragments / progressive builds — needed for teaching decks, the #1 developer use case
- Video embed — expected in any media-capable tool; low complexity (iframe)
- Finish editable PPTX — image-based export is a partial solution; native shapes allow post-generation editing

**Should have (competitive differentiators):**
- Mermaid.js diagram support — developers use Mermaid in every README; they expect it in slides
- Plugin layout system — until v0.4, all layouts live in core; community cannot contribute; this is the ecosystem unlock
- Structured output schemas per layout — gates reliable AI generation; without `maxItems` constraints, LLMs fill slides to maximum capacity
- `generate_presentation(prompt)` MCP tool — highest-value AI feature; no open-source competitor offers this

**Defer (v2+):**
- Real-time collaborative editing (OT/CRDT) — last-writer-wins WebSocket presenter sync is sufficient for v1.0; full CRDT is v2+
- WYSIWYG drag-and-drop editor — destroys the code-as-configuration model and breaks AI generation
- AI content writing / text generation — engine renders, doesn't author; `generate_presentation` delegates content to the calling LLM
- Offline mobile app — viewing works fine on mobile via responsive HTML; editing on mobile is a different product

### Architecture Approach

The architecture follows a "four concentric rings" model. Each ring wraps the existing core build pipeline without modifying it. Ring 1 (v0.3) is template-layer only — new Jinja2 block types and CDN JS libraries, no Python changes. Ring 2 (v0.4) adds `pf/registry.py` for plugin discovery, injected into `PresentationBuilder` via dependency injection — fully backward-compatible. Ring 3 (v0.5) adds `pf/llm_schemas.py` and `pf/optimizer.py` with new MCP tools — no builder changes. Ring 4 (v1.0) adds a `platform/` directory as a separate service that calls `PresentationBuilder` as a library — zero coupling to the existing CLI or MCP server.

**Major components:**
1. `pf/registry.py` (v0.4) — discovers layout, theme, and data source plugins via entry points and directory scanning; injected into builder via DI
2. `pf/llm_schemas.py` (v0.5) — per-layout structured output schemas with `maxItems` generation constraints distinct from the validation schemas in `schema.json`
3. `pf/optimizer.py` (v0.5) — content density optimizer that uses the existing `LayoutAnalyzer` to split overflowing slides; purely algorithmic, no LLM needed
4. `platform/api.py` (v1.0) — FastAPI service wrapping `PresentationBuilder` as a background task; file-based storage first, then S3-compatible
5. `platform/worker.py` (v1.0) — build worker that runs the same `PresentationBuilder` as the CLI; job queue starts with SQLite, moves to Redis at scale

The `pf/` package must remain a pure library with no platform dependencies. The `platform/` directory is an optional service that imports from `pf/` — not the reverse.

### Critical Pitfalls

1. **Mermaid.js async export race condition** — `wait_for_load_state("networkidle")` fires before Mermaid's Promise-based render completes, capturing raw `<pre>` text in PDF/PPTX exports. Fix: add `document.body.dataset.pfReady = 'true'` sentinel after render; replace networkidle wait with `page.wait_for_function("document.body.dataset.pfReady === 'true'")`. Must be solved before Mermaid ships in v0.3.

2. **`autoescape=False` + LLM / hosted API input** — Jinja2 autoescape is disabled for the CLI (users own their YAML). When LLM-generated content or user-submitted data from a REST API reaches templates, this becomes a stored XSS vector. Fix: enable `autoescape=True` for any code path where template variables originate from LLM output or user-submitted data; use `| safe` only on builder-internal HTML. Must be addressed before `generate_presentation` ships in v0.5.

3. **Schema tightening breaks existing decks** — Adding per-layout discriminated unions to `schema.json` (needed for LLM structured output) will break existing `presentation.yaml` files that have extra fields. Fix: per-layout schemas for LLM use (`llm_schemas.py`) must be separate from validation schemas; use `additionalProperties: true` when first introducing per-layout data validation; strict mode is opt-in via `--strict` flag. Must be designed correctly at the start of v0.4.

4. **Plugin CSS leaking into core slides** — Global CSS injection from plugin layouts breaks all slides that don't use that layout. Fix: plugin CSS must be scoped to the slide that uses the layout, injected via `{% block head_extra %}` with layout-prefixed class selectors; never appended to shared `theme/` files. Must be in the plugin spec before the first plugin is written in v0.4.

5. **Hosted platform relative path breakage** — The build output uses relative paths (`theme/variables.css`, `slide_01.html`) that work for `file://` and local `http://` but break when slides are served from a CDN. Fix: add `--base-url` option to the build pipeline that rewrites asset paths before platform upload. Must be added at the end of v0.3 or the start of v1.0, before any upload feature ships.

## Implications for Roadmap

Based on the combined research, the roadmap should follow the four-ring structure exactly as the architecture prescribes, with one critical addition: the `--base-url` path abstraction should be threaded into the end of v0.3 (before v1.0 work begins) so it doesn't require backtracking.

### Phase 1: Rich Media (v0.3)

**Rationale:** Two table-stakes developer features (code highlighting, fragments) are missing. Developer credibility is the prerequisite for ecosystem growth. These are template-layer changes only — low risk, high visibility. Must ship before plugin or LLM work or those layers will be built for an engine that can't render code examples.

**Delivers:** Code highlighting, Mermaid diagrams, video embeds, slide fragments, finish editable PPTX. Optional additions: Google Maps embed, PDF speaker notes. End-of-phase: `--base-url` path abstraction.

**Addresses (FEATURES.md):** Code syntax highlighting (P1), slide fragments (P1), Mermaid diagrams (P1), video embed (P1), editable PPTX completion (P2).

**Avoids (PITFALLS.md):** Mermaid async export race condition (must add `data-pf-ready` sentinel before Mermaid ships); Playwright per-slide browser spawn in `_render_image_fallback()` (fix before expanding native PPTX renderers).

**Stack:** Highlight.js 11.x, Mermaid.js 11.x, Leaflet 1.9.x (all CDN-only); vanilla JS for fragments; no new Python dependencies.

**Research flag:** Standard patterns — well-documented CDN integration, no phase research needed.

### Phase 2: Plugin Ecosystem (v0.4)

**Rationale:** Until plugins exist, all layouts live in core and community cannot contribute. The plugin registry is also a prerequisite for the LLM layer — `list_layouts()` and `get_layout_schema()` must be plugin-aware or a two-tier system emerges. Schema isolation decisions made here (per-layout data schemas, CSS scoping) cannot be easily reversed later.

**Delivers:** `pf/registry.py` (entry point + directory discovery), `PresentationBuilder` registry injection (backward-compatible), `pf plugins` CLI command group, data source plugins interface, updated `list_layouts()` MCP tool.

**Addresses (FEATURES.md):** Layout plugin system (P1), data source plugins (P1), theme plugin system (P2), plugin registry/CLI (P2).

**Avoids (PITFALLS.md):** Schema tightening backward compatibility (design `additionalProperties: true` first); plugin CSS isolation (must be in spec before first plugin); hardcoded `LAYOUT_DESCRIPTIONS` dict in MCP server (move to registry).

**Stack:** `importlib.metadata` entry_points (stdlib); `pluggy 1.6.0` if hook complexity warrants it.

**Research flag:** Entry points pattern is well-documented (HIGH confidence). Data source plugin credential management may need deeper research — OAuth2 for Google Sheets is non-trivial.

### Phase 3: LLM Integration (v0.5)

**Rationale:** Structured schemas must come before `generate_presentation` — without `maxItems` generation constraints, LLMs fill every slide to maximum capacity and overflow warnings hit 60%+ of slides. The content density optimizer (pure algorithmic, no LLM) must also precede the generation tool. This order prevents a generation tool that produces broken output from day one.

**Delivers:** `pf/llm_schemas.py` (per-layout generation schemas with cardinality constraints), `pf/optimizer.py` (content density splitter), new MCP tools: `get_layout_schema()`, `optimize_slide()`, `suggest_layout()`, `generate_from_prompt()`. Also: `autoescape` hardening for LLM input paths.

**Addresses (FEATURES.md):** Structured output schemas per layout (P1), generate_presentation MCP tool (P1), content density optimizer (P1), slide suggestion engine (P2).

**Avoids (PITFALLS.md):** LLM generates overloaded slides (separate LLM schemas from validation schemas; add `maxItems`); `autoescape=False` XSS risk (enable autoescape for LLM code paths before `generate_presentation` ships); `generate_presentation` tool that passes full `schema.json` to LLM (use constrained `llm_schemas.py` instead).

**Stack:** `instructor 1.14.5`, `pydantic 2.12.5`, `anthropic 0.84.0`, `openai 2.25.0` — all as `pf[llm]` optional group.

**Research flag:** `instructor` integration pattern is well-documented (HIGH confidence). Multi-agent workflow contracts and slide suggestion engine heuristics may benefit from phase research — niche problem space.

### Phase 4: Hosted Platform (v1.0)

**Rationale:** Platform depends on plugin ecosystem being stable (hosted builds must match local builds; plugin instability produces unreliable hosted output). Platform also requires the `--base-url` path abstraction from v0.3 — if that wasn't shipped there, it must be the first task here before any upload feature is built. Start with the simplest viable path: synchronous build, file storage, shareable URL. Add async job queue, embed codes, analytics, and collaboration in that order.

**Delivers:** `platform/api.py` (FastAPI service), `platform/worker.py` (build worker), `platform/storage.py` (local fs -> S3/R2 adapter), shareable URL viewer, embed codes, optional analytics beacon, presenter WebSocket sync.

**Addresses (FEATURES.md):** Hosted web viewer (P1), embed codes (P1), REST API (P1), presentation analytics (P2), template marketplace (P2), real-time collaboration presenter sync (P3, last).

**Avoids (PITFALLS.md):** Hosted platform relative path breakage (fix `--base-url` first); API rate limiting for build endpoint (required before public launch); SSE-based live-reload blocks threads (replace with async FastAPI/Starlette for multi-user hosting); Playwright in the API worker for PDF (separate worker pool or defer to client).

**Stack:** `fastapi 0.135.1`, `uvicorn 0.41.0`, `sqlalchemy 2.0.48`, `alembic 1.18.4`, `boto3 1.42.x` — all as `pf[platform]` optional group. SQLite for dev, PostgreSQL for production.

**Research flag:** FastAPI + SQLAlchemy 2.x async patterns are well-documented. Collaboration (WebSocket presenter sync) and real-time analytics are low-complexity for the presenter-push model planned — no phase research needed. Storage adapter pattern (S3/R2/local) is standard.

### Phase Ordering Rationale

- Rich media before plugins because adding new block types in core first validates the template contract that plugin authors will later follow. Dogfooding before opening to external contributors prevents the plugin spec from being designed around theoretical constraints.
- Registry before LLM schemas because the LLM tooling must describe plugin layouts (not just built-ins). Building LLM schemas before the registry forces a rewrite the moment plugins exist.
- Platform last because it requires both plugin stability (consistent build output) and the path abstraction that should be added at the end of v0.3.
- `autoescape` hardening belongs in v0.5 (not deferred to v1.0) because the attack surface opens the moment LLM-generated content reaches templates, which happens in v0.5 — not when the REST API ships.

### Research Flags

Phases needing deeper research during planning:
- **Phase 2 (Plugin Ecosystem):** Google Sheets OAuth2 + Sheets API v4 for the first data source plugin is non-trivial. Credential management for data source plugins in a CLI context needs a clear pattern (keychain? env vars? config file?). Recommend `/gsd:research-phase` for the data source plugin sub-component.
- **Phase 3 (LLM Integration):** Multi-agent workflow contracts and slide suggestion engine heuristics are niche problem spaces with few established patterns. Recommend `/gsd:research-phase` for `suggest_layout()` and multi-agent documentation if those are in scope for the phase.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Rich Media):** CDN JS integration (Highlight.js, Mermaid.js, Leaflet), Playwright sentinel pattern, fragment JS state machine — all well-documented, established patterns.
- **Phase 4 (Platform):** FastAPI + SQLAlchemy 2.x + S3/R2 storage adapter + job queue — standard Python web platform patterns; extensive documentation available.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Python package versions verified via PyPI; JS CDN versions from training data (Aug 2025) — spot-check CDN URLs before v0.3 build |
| Features | MEDIUM | Competitor feature analysis from training data through Aug 2025; Gamma/Beautiful.ai feature sets should be re-verified when web access is available |
| Architecture | HIGH | Based on direct codebase analysis; established Python patterns (entry points, FastAPI, SQLAlchemy 2.x) |
| Pitfalls | HIGH | Derived from direct codebase inspection of `pf/builder.py`, `pf/pptx_native.py`, `pf/pdf.py`, `pf/mcp_server.py`; not generic advice |

**Overall confidence:** HIGH

### Gaps to Address

- **JS CDN library versions:** Highlight.js 11.x, Mermaid.js 11.x, Leaflet 1.9.x versions are from training data. Verify current CDN URLs and latest stable versions before v0.3 build starts.
- **Competitor feature sets:** Gamma and Beautiful.ai feature tables reflect Aug 2025 training data. Re-verify when web access is available — the AI generation features in those products move fast.
- **Data source plugin credential management:** No established pattern researched for how CLI tools manage OAuth2 credentials for data source plugins. Needs resolution before v0.4 data source work starts.
- **`pf serve` SSE threading model:** The current `SimpleHTTPRequestHandler`-based SSE server blocks a thread per client. This is documented as a pitfall for the hosted platform but needs a concrete migration plan before v1.0 lands.
- **Deployment platform selection:** Railway vs. Render vs. Fly.io for the hosted service — pricing and free tier availability should be verified at decision time (v1.0 planning), not now.

## Sources

### Primary (HIGH confidence)
- Codebase direct analysis: `pf/builder.py`, `pf/analyzer.py`, `pf/mcp_server.py`, `pf/pptx_native.py`, `pf/pdf.py`, `pf/schema.json`, `templates/` — architectural patterns and pitfall identification
- PyPI `pip index versions` — instructor (1.14.5), pydantic (2.12.5), fastapi (0.135.1), uvicorn (0.41.0), sqlalchemy (2.0.48), alembic (1.18.4), httpx (0.28.1), pluggy (1.6.0), anthropic (0.84.0), openai (2.25.0)
- Python Packaging Guide entry_points pattern — `importlib.metadata` stdlib, well-documented

### Secondary (MEDIUM confidence)
- Training data through Aug 2025 — instructor, Pydantic v2, FastAPI patterns, Mermaid.js v11 async initialization, Playwright sentinel patterns
- `docs/plans/2026-03-05-roadmap-design.md` and `docs/plans/2026-03-05-editable-pptx-poc.md` — project direction and existing architectural decisions

### Tertiary (LOW confidence)
- Competitor feature analysis (Gamma, Beautiful.ai, Tome) — training data, may be stale; verify before making positioning decisions
- JS CDN library versions (Highlight.js 11.x, Mermaid.js 11.x, Leaflet 1.9.x) — training data cutoff Aug 2025; verify CDN URLs before use

---
*Research completed: 2026-03-05*
*Ready for roadmap: yes*
