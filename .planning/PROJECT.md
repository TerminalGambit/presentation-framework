# Presentation Framework

## What This Is

An open-source presentation engine that generates professional HTML slide decks from YAML configuration and JSON data. AI agents, developers, and non-technical users create branded 1280x720px slide decks through a structured data model — with rich media support, multiple export formats (HTML, PDF, PowerPoint), and first-class MCP server integration for AI workflows.

## Core Value

AI agents and humans can generate high-quality, branded presentations from structured data with a single command or tool call — no manual positioning, no proprietary lock-in.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. Existing v0.2.0 capabilities. -->

- ✓ YAML config + JSON metrics → HTML slides pipeline — v0.2.0
- ✓ 11 slide layouts (title, two-column, three-column, data-table, stat-grid, chart, section, quote, image, timeline, closing) — v0.2.0
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

### Active

<!-- Current scope: v0.3 through v1.0 roadmap -->

- [ ] Rich media: Google Maps embed (interactive HTML, static for exports)
- [ ] Rich media: Video embed (YouTube/Vimeo/MP4)
- [ ] Rich media: Code syntax highlighting (Prism.js or Highlight.js)
- [ ] Rich media: Animated diagrams (Mermaid.js)
- [ ] Rich media: Slide fragments/progressive builds
- [ ] Export: Finish editable PPTX (native renderers for all layouts)
- [ ] Export: PDF speaker notes (annotations or separate pages)
- [ ] Plugin: Layout plugin system (entry points + directory discovery)
- [ ] Plugin: Theme plugin system (installable packages)
- [ ] Plugin: Data source plugins (Google Sheets, APIs, databases)
- [ ] Plugin: Registry and CLI discovery (`pf plugins list/install`)
- [ ] LLM: Structured output schemas per layout
- [ ] LLM: Presentation-from-prompt MCP tool
- [ ] LLM: Slide suggestion engine
- [ ] LLM: Multi-agent workflow documentation
- [ ] LLM: Content density optimizer (auto-split overflowing slides)
- [ ] Accessibility: ARIA labels, alt text, high-contrast mode
- [ ] Platform: Hosted web viewer with shareable URLs
- [ ] Platform: Embed codes (iframe/script)
- [ ] Platform: Presentation analytics (views, engagement)
- [ ] Platform: Real-time collaboration (WebSocket sync)
- [ ] Platform: REST API for build/validate/generate

### Out of Scope

<!-- Explicit boundaries -->

- Native mobile app — web-first, responsive later
- Real-time video conferencing — separate domain, too complex
- AI content writing — engine renders, doesn't author (LLM layer enables this externally)
- Proprietary file formats — open standards only (HTML, PDF, PPTX)
- WYSIWYG visual editor — presentations-as-code is the core philosophy

## Context

- **Existing codebase:** Python 3.10+ CLI built with Click, Jinja2, PyYAML, jsonschema, watchdog
- **Frontend:** CSS Grid/Flexbox, vanilla JS, optional KaTeX and Plotly
- **Exports:** Playwright (PDF/PPTX screenshots), python-pptx (native shapes)
- **Testing:** 57+ pytest tests covering all modules
- **Documentation:** CLAUDE.md (agent workflow), SKILL.md (user guide), README.md
- **Market gap:** No AI-native "presentations as code" tool exists. reveal.js/Marp lack data models; Gamma/Tome are closed SaaS; python-pptx is too low-level
- **Competitors raised:** Gamma ($20M), Tome ($75M), Beautiful.ai ($55M) — all closed platforms

## Constraints

- **Tech stack**: Python + Jinja2 + vanilla JS — no frontend frameworks, keep dependency footprint small
- **Slide dimensions**: Fixed 1280x720px — all layouts designed for this viewport
- **Export fidelity**: HTML is the source of truth; PDF/PPTX are best-effort renderings
- **MCP protocol**: Must maintain MCP server compatibility as the primary AI integration point
- **Backward compatibility**: Existing YAML configs must continue to work across versions

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Bottom-up platform approach (v0.3→v1.0) | Each ring is independently valuable; plugins get battle-tested by own features before opening to others | — Pending |
| Data model: YAML+JSON not Markdown | Structured data enables AI generation, interpolation, schema validation — Markdown can't do this | ✓ Good |
| HTML as source of truth, not PPTX/PDF | Full control over rendering, interactive features, then export to other formats | ✓ Good |
| MCP server as primary AI integration | Standard protocol, works across LLM providers, not tied to one vendor | ✓ Good |
| No frontend framework (vanilla JS) | Minimal dependencies, fast loading, no build step for slide output | ✓ Good |
| Open-source with no monetization yet | Build the best tool first, let the business model emerge from usage patterns | — Pending |

---
*Last updated: 2026-03-05 after project initialization*
