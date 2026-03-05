# Requirements: Presentation Framework

**Defined:** 2026-03-05
**Core Value:** AI agents and humans can generate high-quality, branded presentations from structured data with a single command or tool call.

## v1 Requirements

Requirements for v1.0 release. Each maps to roadmap phases.

### Rich Media

- [ ] **MEDIA-01**: User can add code blocks with syntax highlighting (language-aware coloring via Highlight.js or Prism.js)
- [ ] **MEDIA-02**: User can use slide fragments for progressive reveal (bullet-by-bullet, element-by-element builds)
- [ ] **MEDIA-03**: User can embed Mermaid.js diagrams (flowcharts, sequence diagrams, org charts) in slides
- [ ] **MEDIA-04**: User can embed video (YouTube/Vimeo/MP4) with thumbnail preview in HTML and static frame in exports
- [ ] **MEDIA-05**: User can embed Google Maps with lat/lng, zoom, markers (interactive in HTML, static image in exports)
- [ ] **MEDIA-06**: User can apply custom CSS per individual slide via a `style:` key
- [ ] **MEDIA-07**: User can auto-generate a table of contents slide from section dividers

### Export

- [ ] **EXPORT-01**: PDF/PPTX export correctly renders async JS content (Mermaid, Prism) via `data-pf-ready` sentinel
- [ ] **EXPORT-02**: PPTX native renderer supports all 11 layouts (not just title/section/quote/closing)
- [ ] **EXPORT-03**: PDF export includes speaker notes as annotations or separate notes pages
- [ ] **EXPORT-04**: PPTX native export reuses single browser context instead of spawning per-slide

### Plugin Ecosystem

- [ ] **PLUG-01**: Developer can create and register custom layout plugins via Python entry points or `layouts/` directory
- [ ] **PLUG-02**: Developer can create and distribute installable theme packages (`pip install pf-theme-<name>`)
- [ ] **PLUG-03**: Developer can create data source plugins connecting to Google Sheets, REST APIs, and databases
- [ ] **PLUG-04**: User can discover and install plugins via CLI (`pf plugins list`, `pf plugins install <name>`)
- [ ] **PLUG-05**: Layout plugins support template inheritance (base layout → variant pattern)
- [ ] **PLUG-06**: Plugin CSS is isolated to prevent style leaks into core slides or other plugins

### LLM Integration

- [ ] **LLM-01**: Each layout has a documented JSON Schema with constraints (maxItems, maxLength) for LLM structured output
- [ ] **LLM-02**: MCP server provides `generate_presentation(prompt, style, length)` tool that outputs valid YAML+JSON
- [ ] **LLM-03**: MCP server provides slide suggestion tool (given partial deck, suggests next slides based on content flow)
- [ ] **LLM-04**: Multi-agent workflow (researcher → data → layout → review) is documented and tested
- [ ] **LLM-05**: Content density optimizer auto-splits overflowing slides and redistributes content across layouts
- [ ] **LLM-06**: Accessibility checker validates ARIA labels, generates alt text, and supports high-contrast mode
- [ ] **LLM-07**: Jinja2 templates use selective autoescaping for LLM-generated content to prevent XSS

### Platform

- [ ] **PLAT-01**: User can upload or link a deck to get a shareable URL with full navigator experience
- [ ] **PLAT-02**: User can embed presentations via iframe or script tag in blogs, Notion, and docs
- [ ] **PLAT-03**: Platform tracks presentation analytics (views, slide-level engagement, time-per-slide)
- [ ] **PLAT-04**: Multiple users can edit the same presentation with real-time WebSocket sync
- [ ] **PLAT-05**: REST API provides HTTP endpoints for build, validate, and generate operations
- [ ] **PLAT-06**: Build output supports configurable base URL for CDN/hosted asset paths (`--base-url`)

## v2 Requirements

Deferred to future release.

### Advanced Collaboration

- **COLLAB-01**: User can leave comments on specific slides
- **COLLAB-02**: User can see revision history with visual diff
- **COLLAB-03**: User can branch/fork presentations

### Marketplace

- **MARKET-01**: Web-based plugin/theme marketplace with search and ratings
- **MARKET-02**: One-click install from marketplace to local CLI
- **MARKET-03**: Developer can publish plugins to marketplace

### Advanced Export

- **ADVEX-01**: User can export to Google Slides format
- **ADVEX-02**: User can export animated GIF/video of slide transitions
- **ADVEX-03**: White-label embedding SDK for third-party apps

## Out of Scope

| Feature | Reason |
|---------|--------|
| Native mobile app | Web-first; responsive design handles mobile viewing |
| Real-time video conferencing | Separate domain, massive complexity, existing tools solve this |
| AI content writing/authoring | Engine renders, doesn't author; LLM layer enables external authoring |
| Proprietary file formats | Open standards only (HTML, PDF, PPTX) |
| WYSIWYG visual editor | Presentations-as-code is the core philosophy |
| Database-backed storage for v1 core | Flat files are the source of truth; platform layer adds optional persistence |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| MEDIA-01 | Phase 1 | Pending |
| MEDIA-02 | Phase 1 | Pending |
| MEDIA-03 | Phase 1 | Pending |
| MEDIA-04 | Phase 1 | Pending |
| MEDIA-05 | Phase 1 | Pending |
| MEDIA-06 | Phase 1 | Pending |
| MEDIA-07 | Phase 1 | Pending |
| EXPORT-01 | Phase 1 | Pending |
| EXPORT-02 | Phase 1 | Pending |
| EXPORT-03 | Phase 1 | Pending |
| EXPORT-04 | Phase 1 | Pending |
| PLUG-01 | Phase 2 | Pending |
| PLUG-02 | Phase 2 | Pending |
| PLUG-03 | Phase 2 | Pending |
| PLUG-04 | Phase 2 | Pending |
| PLUG-05 | Phase 2 | Pending |
| PLUG-06 | Phase 2 | Pending |
| LLM-01 | Phase 3 | Pending |
| LLM-02 | Phase 3 | Pending |
| LLM-03 | Phase 3 | Pending |
| LLM-04 | Phase 3 | Pending |
| LLM-05 | Phase 3 | Pending |
| LLM-06 | Phase 3 | Pending |
| LLM-07 | Phase 3 | Pending |
| PLAT-01 | Phase 4 | Pending |
| PLAT-02 | Phase 4 | Pending |
| PLAT-03 | Phase 4 | Pending |
| PLAT-04 | Phase 4 | Pending |
| PLAT-05 | Phase 4 | Pending |
| PLAT-06 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 30 total
- Mapped to phases: 30
- Unmapped: 0

---
*Requirements defined: 2026-03-05*
*Last updated: 2026-03-06 — traceability filled in after roadmap creation*
