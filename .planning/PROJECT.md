# Presentation Framework

## What This Is

An open-source presentation engine that generates professional HTML slide decks from YAML configuration and JSON data. AI agents, developers, and non-technical users create branded 1280x720px slide decks through a structured data model — with 16 slide layouts, rich media support (code, diagrams, video, maps), multiple export formats (HTML, PDF, PowerPoint), a plugin ecosystem, LLM-native generation tools, and a hosted platform with shareable URLs and real-time sync.

## Core Value

AI agents and humans can generate high-quality, branded presentations from structured data with a single command or tool call — no manual positioning, no proprietary lock-in.

## Requirements

### Validated

<!-- Shipped and confirmed valuable -->

- ✓ YAML config + JSON metrics → HTML slides pipeline — v0.2.0
- ✓ 11 base slide layouts (title, two-column, three-column, data-table, stat-grid, chart, section, quote, image, timeline, closing) — v0.2.0
- ✓ Metrics interpolation (`{{ metrics.path }}`) for data-driven slides — v0.1.0
- ✓ Theme system with primary/accent colors, fonts, and style presets — v0.1.0
- ✓ Interactive Plotly.js charts (bar, line, pie, scatter) — v0.2.0
- ✓ KaTeX math rendering (inline and display) — v0.2.0
- ✓ Speaker notes with keyboard toggle — v0.2.0
- ✓ Per-slide transitions (fade, slide, zoom, flip) — v0.2.0
- ✓ PDF export via Playwright — v0.2.0
- ✓ PowerPoint export (image-based + partial native editable) — v0.2.0
- ✓ WCAG contrast checker with build-time warnings — v0.2.0
- ✓ MCP server with 6 tools (build, validate, contrast, layouts, examples, init) — v0.2.0
- ✓ Image lightbox (click to zoom) — v0.2.0
- ✓ Live-reload dev server (SSE) — v0.1.0
- ✓ Layout density analyzer with overflow warnings — v0.1.0
- ✓ JSON Schema validation for YAML config — v0.1.0
- ✓ Keyboard navigation, grid overview, fullscreen — v0.1.0
- ✓ Code syntax highlighting (Highlight.js) — v0.2
- ✓ Slide fragments / progressive builds — v0.2
- ✓ Mermaid.js diagram embedding — v0.2
- ✓ Video embedding (YouTube/Vimeo/MP4) — v0.2
- ✓ Google Maps embedding (Leaflet/OSM) — v0.2
- ✓ Per-slide custom CSS — v0.2
- ✓ Auto-generated TOC from section dividers — v0.2
- ✓ data-pf-ready sentinel for async export — v0.2
- ✓ Native PPTX renderers for 10/11 layouts — v0.2
- ✓ PDF speaker notes as interleaved pages — v0.2
- ✓ Shared browser context for PPTX export — v0.2
- ✓ Layout plugin system (entry points + directory) — v0.2
- ✓ Theme plugin packages (`pip install pf-theme-*`) — v0.2
- ✓ Data source plugins (fetch + merge into metrics) — v0.2
- ✓ Plugin CLI (`pf plugins list/install/info`) — v0.2
- ✓ Template inheritance for plugin layouts — v0.2
- ✓ Plugin CSS isolation (.pf-layout-{name}) — v0.2
- ✓ LLM structured output schemas per layout (Pydantic v2) — v0.2
- ✓ `generate_presentation` MCP tool with XSS sanitization — v0.2
- ✓ `suggest_layout` MCP tool — v0.2
- ✓ Multi-agent workflow documented and tested — v0.2
- ✓ Content density optimizer (auto-split overflowing slides) — v0.2
- ✓ Accessibility checker (ARIA, alt text, high-contrast mode) — v0.2
- ✓ Jinja2 XSS hardening for LLM content (bleach + regex fallback) — v0.2
- ✓ Hosted platform with shareable URLs — v0.2
- ✓ iframe embedding with CSP headers — v0.2
- ✓ Analytics tracking (SQLite, per-slide engagement) — v0.2
- ✓ WebSocket presenter sync — v0.2
- ✓ REST API (build, validate, embed endpoints) — v0.2
- ✓ Configurable `--base-url` for CDN/hosted paths — v0.2

### Active

<!-- Next milestone scope -->

(None yet — define with `/gsd:new-milestone`)

### Out of Scope

- Native mobile app — web-first, responsive later
- Real-time video conferencing — separate domain, too complex
- AI content writing — engine renders, doesn't author (LLM layer enables this externally)
- Proprietary file formats — open standards only (HTML, PDF, PPTX)
- WYSIWYG visual editor — presentations-as-code is the core philosophy
- Database-backed storage for core — flat files are source of truth; platform layer adds optional persistence

## Context

- **Shipped:** v0.2 milestone (v1.0 feature complete) on 2026-03-07
- **Codebase:** 11,528 lines Python across 30+ modules
- **Tech stack:** Python 3.10+ CLI (Click, Jinja2, PyYAML, jsonschema, watchdog), FastAPI platform, Pydantic v2 schemas
- **Frontend:** CSS Grid/Flexbox, vanilla JS, optional KaTeX/Plotly/Highlight.js/Mermaid/Leaflet CDN
- **Exports:** Playwright (PDF/PPTX screenshots), python-pptx (native shapes)
- **Testing:** 482 pytest tests, all passing
- **Platform:** FastAPI + SQLite analytics + WebSocket sync
- **Known tech debt:** Beacon/sync script injection, LLM schemas for 5 new layouts, Vimeo oEmbed

## Constraints

- **Tech stack**: Python + Jinja2 + vanilla JS — no frontend frameworks, keep dependency footprint small
- **Slide dimensions**: Fixed 1280x720px — all layouts designed for this viewport
- **Export fidelity**: HTML is the source of truth; PDF/PPTX are best-effort renderings
- **MCP protocol**: Must maintain MCP server compatibility as the primary AI integration point
- **Backward compatibility**: Existing YAML configs must continue to work across versions

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Bottom-up platform approach (v0.3→v1.0) | Each ring independently valuable; plugins battle-tested by own features | ✓ Good — all 4 rings shipped cleanly |
| Data model: YAML+JSON not Markdown | Structured data enables AI generation, interpolation, schema validation | ✓ Good |
| HTML as source of truth, not PPTX/PDF | Full control over rendering, interactive features, then export | ✓ Good |
| MCP server as primary AI integration | Standard protocol, works across LLM providers | ✓ Good |
| No frontend framework (vanilla JS) | Minimal dependencies, fast loading, no build step | ✓ Good |
| Four concentric rings architecture | Rich Media → Plugins → LLM → Platform; each leaves PresentationBuilder untouched | ✓ Good — clean separation maintained |
| data-pf-ready sentinel for async content | Mermaid/code need async init; sentinel gates export capture | ✓ Good — solved export race conditions |
| XSS hardening in Phase 3 not Phase 4 | Attack surface opens when LLM content hits templates | ✓ Good — bleach + regex fallback |
| PluginRegistry auto-discover in __init__ | Zero-config for users; entry points + local dirs | ✓ Good |
| pf_platform/ not platform/ | Avoid shadowing Python stdlib platform module | ✓ Good — caught and fixed during Phase 4 |
| Chart layout uses screenshot PPTX fallback | Interactive Plotly cannot be meaningfully represented as static shapes | ✓ Good — documented decision |
| Open-source with no monetization yet | Build the best tool first, let the business model emerge | — Pending |

---
*Last updated: 2026-03-07 after v0.2 milestone*
