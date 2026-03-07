# Milestones

## v0.2 — v1.0 Feature Complete (Shipped: 2026-03-07)

**Phases completed:** 4 phases, 21 plans
**Git range:** 74 commits, 106 files changed, 17,465 insertions
**Lines of code:** 11,528 Python
**Timeline:** 7 days (2026-02-28 → 2026-03-07)
**Tests:** 482 passing

**Key accomplishments:**
1. Rich media support — code highlighting (Highlight.js), Mermaid diagrams, video/map embeds, fragment reveals, auto-generated TOC
2. Full native PPTX export for 10/11 layouts with editable shapes (chart intentionally uses screenshot fallback)
3. Plugin ecosystem — layout, theme, and data source plugins via Python entry points with CLI discovery (`pf plugins`)
4. LLM integration — constrained Pydantic schemas per layout, content density optimizer, `generate_presentation` MCP tool with XSS sanitization
5. Hosted platform — FastAPI service with shareable URLs, iframe embedding, REST API, SQLite analytics, WebSocket presenter sync
6. Accessibility — ARIA labels, alt text generation, high-contrast mode toggle, `check_accessibility_output` MCP tool

**Known tech debt:**
- BEACON_SCRIPT and SYNC_SCRIPT not auto-injected into served `present.html`
- 5 Phase 1 layouts (code, mermaid, video, map, toc) missing from LLM schemas/descriptions
- 4 SUMMARY frontmatter gaps (MEDIA-02, MEDIA-07, PLUG-04, PLAT-04)
- Vimeo oEmbed thumbnail placeholder

**Audit:** .planning/milestones/v0.2-MILESTONE-AUDIT.md (status: tech_debt, 30/30 requirements)

---

