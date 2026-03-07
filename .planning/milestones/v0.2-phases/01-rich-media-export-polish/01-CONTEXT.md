# Phase 1: Rich Media + Export Polish - Context

**Gathered:** 2026-03-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Add code highlighting, Mermaid diagrams, video embeds, Google Maps, slide fragments, per-slide CSS, and auto-generated TOC slides. Finish the export pipeline with all-layout native PPTX, PDF speaker notes, async sentinel fix, and shared browser context. 11 requirements: MEDIA-01 through MEDIA-07, EXPORT-01 through EXPORT-04.

</domain>

<decisions>
## Implementation Decisions

### Code block integration
- Both a `code` block type (for two-column/three-column layouts) AND a dedicated full-slide `code` layout
- Highlight.js theme auto-matches slide background color using existing `_is_light()` detection — dark theme on dark slides, light theme on light slides
- Line numbers optional, off by default — users add `line_numbers: true` per code block
- Auto-detect from slides: builder scans for code blocks and injects Highlight.js CDN automatically — no `theme.code` flag needed

### Fragment reveal model
- Both per-bullet and per-block granularity — `fragment: true` on a bullet reveals that bullet; on a block reveals the whole block
- Arrow keys are context-aware: right arrow reveals next fragment first, then advances to next slide when all fragments shown (reveal.js / PowerPoint model)
- Animation: fade + slide up (opacity 0→1 with subtle upward translation)
- Fragment JS state machine always included in every build (no flag, no detection — it's small enough)

### Embed authoring model
- Mermaid: Both `mermaid` block type AND dedicated full-slide `mermaid` layout
- Video: Both `video` block type AND dedicated full-slide `video` layout — auto-detects YouTube/Vimeo/MP4 from URL
- Maps: Both `map` block type AND dedicated full-slide `map` layout — data shape includes lat, lng, zoom, markers
- All new rich media types use auto-detect for CDN loading — builder scans slides and includes only needed libraries (Highlight.js, Mermaid.js, Leaflet)
- Existing `theme.math` and `theme.charts` flags stay as-is for backward compatibility

### Export fallback strategy
- Video in PDF/PPTX: Thumbnail image with centered play icon overlay — auto-fetch thumbnail for YouTube/Vimeo, first frame for MP4. Link to video URL in PPTX notes
- Mermaid in PDF/PPTX: Playwright renders the SVG using `data-pf-ready` sentinel — wait for Mermaid.js to finish rendering, then capture
- Maps in PDF/PPTX: Playwright screenshot of live Leaflet map — wait for tile loading, then capture
- Code in PDF/PPTX: Playwright captures the syntax-highlighted output

### Claude's Discretion
- PPTX native vs image per rich media content type — Claude picks the best trade-off (native shapes for text-heavy layouts, images for code/mermaid/maps/video as appropriate)
- Specific Highlight.js dark/light theme names
- Fragment animation timing and easing
- Mermaid theme/styling defaults
- Map tile provider choice for Leaflet
- Per-slide CSS implementation details (`style:` key parsing)
- Auto-generated TOC slide design and section detection logic

</decisions>

<specifics>
## Specific Ideas

- Rich media pattern: every new media type (code, mermaid, video, map) follows the same dual approach — usable as a block type in columnar layouts AND as a dedicated full-slide layout
- Auto-detect pattern for CDN loading replaces explicit theme flags for all Phase 1 additions — builder scans slides to determine which libraries to include
- Fragment navigation should feel like PowerPoint/reveal.js — arrow keys handle both fragments and slides contextually

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_is_light()` in builder.py: Detects light vs dark backgrounds — use for auto-selecting Highlight.js theme
- `base.html.j2`: Conditional CDN loading pattern (KaTeX via `theme.math`, Plotly via `theme.charts`) — extend with auto-detect blocks
- `LayoutAnalyzer`: Overflow detection for columnar layouts — needs updating to estimate code/mermaid/video/map block heights
- `present.html.j2`: Keyboard navigation handler — needs fragment state machine integration

### Established Patterns
- Theme flags (`theme.math`, `theme.charts`): Existing explicit opt-in for CDN libraries — Phase 1 shifts to auto-detect but keeps these for backward compatibility
- Layout templates: Each layout is a standalone Jinja2 template extending `base.html.j2` — new code/mermaid/video/map layouts follow this pattern
- Block types in columnar layouts: Two-column uses `left`/`right` lists of typed blocks (card, table, stat-grid, etc.) — new block types plug into this

### Integration Points
- `PresentationBuilder.build()`: Needs pre-render scan of slides to determine which CDNs to auto-include
- `base.html.j2 {% block head_extra %}`: Insertion point for auto-detected CDN scripts
- `pdf.py` / `pptx.py`: Need `data-pf-ready` sentinel support for async content (Mermaid, maps)
- `schema.json`: Needs updating with new block types, layout definitions, and fragment keys

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-rich-media-export-polish*
*Context gathered: 2026-03-06*
