# Presentation Framework Roadmap

**Date:** 2026-03-05
**Status:** Approved
**Current Version:** 0.2.0

## Vision

The open-source presentation engine for the AI era. A modular, extensible system where AI agents and humans create professional slide decks from structured data — with rich media, multiple export formats, and a plugin ecosystem.

## Market Context

No serious "presentations as code" tool is designed for AI agents. The landscape:

- **reveal.js / Marp / Slidev** — Developer-focused, Markdown-based. No structured data model, no MCP, no agent workflow.
- **Google Slides API / PowerPoint COM** — API-driven but low-level. Hundreds of API calls for basic positioning.
- **Gamma / Beautiful.ai / Tome** — AI-powered but closed SaaS. Not engines you can embed or extend.
- **python-pptx / Apache POI** — Libraries, not tools. Raw rectangle drawing.

**Presentation Framework** occupies the unique intersection: structured data model (YAML+JSON), high-quality HTML output, multiple export formats, and a first-class MCP server for AI agents.

## Approach: Bottom-Up Platform

Build outward from the engine in concentric rings. Each milestone is independently valuable.

```
v0.3: Rich Media & Polish  →  The Canvas
v0.4: Plugin Architecture  →  The Ecosystem
v0.5: LLM Integration      →  The AI Brain
v1.0: Platform Layer        →  The Product
```

---

## v0.3 — Rich Media & Polish (The Canvas)

**Goal:** Make the slide canvas powerful enough that you never need to say "we can't render that."

### High Priority

| Feature | Description |
|---------|-------------|
| Google Maps embed | New `map` layout or content block. Lat/lng, zoom, markers, style. Static image for PDF/PPTX, interactive in HTML. |
| Video embed | Content block for YouTube/Vimeo/MP4. Thumbnail + play button in HTML, static frame in exports. |
| Code syntax highlighting | Content block with Prism.js or Highlight.js. Language-aware coloring. |

### Medium Priority

| Feature | Description |
|---------|-------------|
| Animated diagrams | Mermaid.js or D3 for flowcharts, sequence diagrams, org charts. |
| Finish editable PPTX | Complete native renderers for two-column, three-column, data-table. |
| PDF speaker notes | Include notes as PDF annotations or separate notes pages. |
| Slide fragments/builds | Progressive reveal within a slide (bullet-by-bullet, element-by-element). |

### Low Priority

| Feature | Description |
|---------|-------------|
| Custom CSS per slide | `style:` key on individual slides for one-off customization. |
| Auto table of contents | Generate TOC slide from section dividers. |

---

## v0.4 — Plugin Architecture (The Ecosystem)

**Goal:** Anyone can create and distribute layouts, themes, and data connectors without touching core.

### High Priority

| Feature | Description |
|---------|-------------|
| Layout plugin system | Custom layouts via Python entry points or `layouts/` directory. Plugin = Jinja2 template + optional CSS/JS + schema. |
| Theme plugin system | Installable theme packages. `pip install pf-theme-corporate`. |
| Data source plugins | Connect to Google Sheets, Airtable, REST APIs, databases. Resolves `{{ data.source_name.query }}` at build time. |

### Medium Priority

| Feature | Description |
|---------|-------------|
| Plugin registry/discovery | `pf plugins list`, `pf plugins install <name>`. Simple JSON registry. |
| Template inheritance | Layouts extend other layouts. Base → variant pattern. |

### Low Priority

| Feature | Description |
|---------|-------------|
| Hook system | Pre-build / post-build hooks for image optimization, link checking, etc. |

---

## v0.5 — LLM Integration Layer (The AI Brain)

**Goal:** The best presentation engine for AI agents, with structured schemas and multi-agent workflows.

### High Priority

| Feature | Description |
|---------|-------------|
| Structured output schemas | JSON Schema per layout for constrained LLM decoding. |
| Presentation-from-prompt | MCP tool: `generate_presentation(prompt, style, length)` → full YAML+JSON. |

### Medium Priority

| Feature | Description |
|---------|-------------|
| Slide suggestion engine | Given partial deck, suggest next slides based on flow and audience. |
| Multi-agent workflow | Researcher → data → layout → review agent pipeline. |
| Content density optimizer | Auto-split overflowing slides, redistribute content across layouts. |
| Accessibility checker | ARIA labels, alt text generation, high-contrast mode. |

### Low Priority

| Feature | Description |
|---------|-------------|
| Version diffing | Compare two deck versions, show changes. |

---

## v1.0 — Platform Layer (The Product)

**Goal:** From CLI tool to web-accessible platform with sharing, analytics, and collaboration.

### High Priority

| Feature | Description |
|---------|-------------|
| Hosted web viewer | Upload/link a deck, get shareable URL with full navigator. |
| Embed codes | `<iframe>` and `<script>` embeds for blogs, Notion, docs. |

### Medium Priority

| Feature | Description |
|---------|-------------|
| Presentation analytics | Track views, slide-level engagement, time-per-slide. |
| Real-time collaboration | WebSocket sync for multiple editors. |
| Template marketplace | Browse and install community themes/layouts. |
| REST API | HTTP endpoints for build, validate, generate. |

### Low Priority

| Feature | Description |
|---------|-------------|
| White-label/embedding SDK | JavaScript SDK for embedding the builder in other apps. |

---

## Business Model Assessment

### Market Opportunity

AI presentation generation is a hot market (Gamma $20M, Tome $75M, Beautiful.ai $55M raised — all closed SaaS). Clear gap for an open-source engine AI developers can build on.

### Potential Models

| Model | Mechanism | Fit |
|-------|-----------|-----|
| Open core + hosted API | Free engine, paid hosted build/generate API (per-build pricing) | Strong |
| Managed platform | Hosted viewer + analytics + collaboration SaaS | Strong (post v1.0) |
| Premium plugins/themes | Paid professional theme packs, industry templates | Medium |
| Enterprise licensing | On-prem with support, custom branding, SSO | Medium-long term |
| Consulting/integration | Help companies integrate the engine | Immediate |

### Competitive Moat

Structured data model + MCP server combination. No other tool lets an AI agent generate a presentation from structured data with a single tool call.

### Risks

- **Timing:** Google/Microsoft could add AI-native APIs to Slides/PowerPoint
- **Adoption:** Open-source presentation tools historically struggle (Marp ~6K stars after 7 years)
- **Mitigation:** MCP angle is genuinely novel. Focus on being the best tool for AI agents.

---

## Current State (v0.2.0)

Completed features that form the foundation:

- 11 slide layouts (title, two-column, three-column, data-table, stat-grid, chart, section, quote, image, timeline, closing)
- Interactive Plotly.js charts
- KaTeX math rendering
- Speaker notes (inline, no cross-origin issues)
- Per-slide transitions (fade, slide, zoom, flip)
- PDF export (Playwright)
- PowerPoint export (image-based + partial native editable)
- WCAG contrast checker
- MCP server (6 tools)
- Image lightbox
- Live-reload dev server
- 57+ passing tests
