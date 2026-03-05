# Feature Research

**Domain:** Presentation engine / AI-native slide deck generator
**Researched:** 2026-03-05
**Confidence:** MEDIUM (web tools unavailable; based on training data through August 2025 + codebase analysis)

---

## Framing: Three Target Users

This engine serves three distinct user personas, each with different expectations:

1. **AI Agents** — The primary novel market. Agents calling MCP tools to generate decks programmatically. Expect: structured schemas, deterministic output, no hallucination-prone free text, fast build API.
2. **Developers** — Building on top of the engine or creating decks as code. Expect: CLI, version control friendliness, plugin extensibility, code highlighting, diagrams.
3. **General Users** — Handed a CLI or hosted UI, creating one-off decks. Expect: templates, easy theming, sharing links, export to familiar formats (PDF, PPTX).

Table stakes differ by persona. What's table stakes for developers (code highlighting) is a differentiator for general users.

---

## Feature Landscape

### Table Stakes — All Users

Features any presentation tool is expected to have. Missing these = immediate credibility loss.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Multiple export formats (PDF, PPTX) | Users need to send decks to people who don't have the tool | MEDIUM | Already shipped v0.2.0 |
| Keyboard navigation | Every presentation tool has this | LOW | Already shipped v0.1.0 |
| Speaker notes | Standard presenter feature since PowerPoint 97 | LOW | Already shipped v0.2.0 |
| Themes / branding | Users expect colors, fonts, logo control | MEDIUM | Already shipped v0.1.0 |
| Fullscreen mode | Standard presentation mode | LOW | Already shipped v0.1.0 |
| Slide transitions | Expectation set by PowerPoint/Keynote | LOW | Already shipped v0.2.0 |
| Image support | Visual slides are the norm | LOW | Already shipped; lightbox v0.2.0 |
| Grid overview / thumbnail navigator | PowerPoint/Keynote train this expectation | LOW | Already shipped v0.1.0 |
| Code syntax highlighting | Any developer-adjacent tool must highlight code | LOW | Not yet built — HIGH PRIORITY gap |
| Live reload during authoring | Standard DX for any code-based authoring tool | LOW | Already shipped v0.1.0 |
| Validation with clear errors | YAML authors need to know what's wrong | LOW | Already shipped v0.1.0 |

### Table Stakes — Developer Users

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Code blocks with syntax highlighting | Core developer expectation; reveal.js, Marp, Slidev all have this | LOW | Not yet built — use Prism.js or Highlight.js |
| Diagram support (flowcharts, sequence) | Developers use Mermaid in every other markdown doc; expect it here | MEDIUM | Mermaid.js integration planned v0.3 |
| CLI-first workflow | Developers don't want a GUI; command line is home | LOW | Already shipped |
| Version control friendly output | Plain text config, deterministic HTML output | LOW | Already achieved by design |
| Plugin / extension points | Developers want to add custom layouts without forking | HIGH | Planned v0.4 — critical for ecosystem |

### Table Stakes — AI Agent Users

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| MCP tool interface | The standard AI tool protocol in 2025-2026 | MEDIUM | Already shipped v0.2.0 |
| Structured schemas per layout | Agents need constrained output — free-form YAML causes hallucinations | MEDIUM | Planned v0.5 — critical |
| Validation on every build | Agents can't "look at it and fix it"; must fail loudly | LOW | Already shipped |
| Idempotent builds | Same input → same output (no timestamp-based filenames, etc.) | LOW | Already achieved by design |
| Programmatic build API | Agents call a function, not a shell command | MEDIUM | MCP covers this; REST API for non-MCP agents |

### Table Stakes — General Users

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Shareable link / hosted view | "Can you send me the deck?" is the most common post-presentation request | HIGH | Planned v1.0 — significant infrastructure |
| Embed in docs/notion | Notion, Confluence, personal sites expect iframe embed | MEDIUM | Planned v1.0 |
| Templates to start from | General users don't start from a blank YAML | MEDIUM | Templates exist via `pf init`; needs richer library |

---

### Differentiators — AI Agent Targeting

Features that directly serve the AI-native positioning. No competitor has these.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Structured output schemas per layout | Eliminates hallucinated YAML structure; agents get a JSON Schema to constrain generation | MEDIUM | Planned v0.5. Major unlock for reliability |
| `generate_presentation(prompt)` MCP tool | One tool call → full deck. No competitor offers this with structured data model | HIGH | Planned v0.5. Highest-value AI feature |
| Multi-agent workflow support | Researcher → data → slide → review pipeline with handoff contracts | HIGH | Planned v0.5. Genuinely novel |
| Content density optimizer | Auto-splits overflowing slides; agents can't visually inspect output | MEDIUM | Planned v0.5. Agents need this since they don't see the output |
| Slide suggestion engine | Given a partial deck, suggest next slides — acts as creative partner for agents | HIGH | Planned v0.5. Differentiates from passive engines |

### Differentiators — Developer Targeting

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Data model separation (YAML + JSON) | Structured metrics separated from layout — no other tool does this cleanly | LOW | Already shipped. Unique. |
| Plugin layout system | Custom layouts as Python packages; distribute via pip | HIGH | Planned v0.4. Enables community ecosystem |
| Data source plugins | Pull from Google Sheets, APIs, databases at build time | HIGH | Planned v0.4. Major workflow unlock for data teams |
| Theme packages (`pip install pf-theme-corporate`) | First-class theme distribution via PyPI | MEDIUM | Planned v0.4 |
| Animated diagrams (Mermaid.js) | Flowcharts, sequence diagrams, org charts in slides | MEDIUM | Planned v0.3 |
| Slide fragments / progressive builds | Bullet-by-bullet reveal; teach complex concepts | MEDIUM | Planned v0.3 |
| Editable PPTX export | True native PowerPoint shapes (not images) for post-generation editing | HIGH | Partially shipped; completing v0.3 |
| Google Maps embed | Interactive maps in slides — rare in any presentation tool | MEDIUM | Planned v0.3 |

### Differentiators — Platform / General Users

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Hosted web viewer | Shareable URL for HTML decks; solves the "send me the deck" problem without PDF | HIGH | Planned v1.0 |
| Presentation analytics | Time-per-slide, view counts — helps presenters know what lands | MEDIUM | Planned v1.0 |
| Real-time collaboration | WebSocket multi-editor sync; rare in code-based tools | HIGH | Planned v1.0. High cost, validate need first |
| Template marketplace | Community browse/install for themes and layouts | MEDIUM | Planned v1.0 |

---

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| WYSIWYG drag-and-drop editor | "I just want to click and edit" | Destroys the code-as-configuration model; breaks AI generation, version control, idempotency | Invest in better templates and `pf init` scaffolding instead |
| Real-time video conferencing | "Can I present live through the tool?" | Entirely separate domain; WebRTC is a 6-month project; competing with Zoom/Meet is a trap | Use share link + Zoom screenshare; tool stays a deck engine |
| AI content writing / text generation | "Write my slides for me" | Engine renders, doesn't author; AI writing quality varies wildly; support cost is infinite | Provide `generate_presentation(prompt)` MCP tool that delegates content to the calling LLM — agent writes content, engine renders |
| Offline-first mobile app | "I want to edit on my phone" | High cost, entirely different UI paradigm; mobile editing of YAML is unusable | Ship the web viewer first; responsive HTML output works on mobile for viewing |
| Proprietary binary format | "Can you make a .pf file?" | Lock-in; can't version control; breaks all export pipelines | Stay on open standards (YAML, HTML, PDF, PPTX) |
| Real-time collaborative editing with OT/CRDT | "Like Google Docs but for slides" | Operational transformation on YAML + rendered HTML is extremely complex; operational cost is high | Ship WebSocket sync (simpler last-writer-wins first); defer true OT to v2+ |
| Built-in presentation hosting (like Speaker Deck) | "Make it like Speaker Deck" | Speaker Deck charges for it; storage, CDN, auth is a platform not a feature | Lightweight hosted viewer is fine; don't try to be a full SaaS presentation host in v1.0 |
| Per-slide animations (non-transition) | "Make this chart animate on scroll" | CSS animation authoring in YAML is a DSL nightmare; accessibility problems | Slide fragments (progressive builds) cover 80% of the need without animation complexity |

---

## Feature Dependencies

```
Code Syntax Highlighting
    └──enables──> Code Layout Block
                      └──enables──> Developer Adoption

Mermaid.js Integration
    └──enables──> Diagram Layout Block

Plugin Layout System (v0.4)
    └──requires──> Plugin registry / discovery
    └──requires──> Entry points standard (importlib.metadata)
    └──enables──> Theme Plugin System
    └──enables──> Community Ecosystem

Data Source Plugins (v0.4)
    └──requires──> Plugin Layout System (same entry point mechanism)
    └──enables──> Google Sheets connector
    └──enables──> REST API connector

Structured Output Schemas (v0.5)
    └──requires──> All layouts have stable, documented schemas
    └──enables──> generate_presentation(prompt) MCP tool
    └──enables──> Slide Suggestion Engine
    └──enables──> Content Density Optimizer (knows schema constraints)

generate_presentation(prompt) (v0.5)
    └──requires──> Structured Output Schemas
    └──requires──> MCP server (already exists)
    └──enhances──> All AI agent workflows

Hosted Web Viewer (v1.0)
    └──requires──> REST API (build + upload)
    └──enables──> Shareable URLs
    └──enables──> Embed Codes
    └──enables──> Presentation Analytics

REST API (v1.0)
    └──enables──> Hosted Web Viewer
    └──enables──> Third-party integrations
    └──enables──> Non-MCP AI agents (e.g., LangChain, CrewAI callers)

Real-time Collaboration (v1.0)
    └──requires──> Hosted Web Viewer (shared context)
    └──requires──> Auth layer (who is editing)
    └──conflicts──> Code-as-configuration model (local file = source of truth)

Plugin Registry (v0.4)
    └──requires──> Plugin Layout System
    └──enhances──> Theme Plugin System
```

### Dependency Notes

- **Code highlighting must precede any code layout block:** Prism.js or Highlight.js must be bundled before a `code` content block type can be introduced. This is a v0.3 prerequisite.
- **Plugin system gates ecosystem growth:** Until v0.4, all layouts live in core. Community can't contribute. Plugin system is the unlock for ecosystem velocity.
- **Structured schemas gate AI reliability:** An LLM calling `build_presentation` without constrained schemas will hallucinate YAML structure. Schemas in v0.5 make AI generation production-grade.
- **Hosted viewer conflicts with code-as-config:** When a local YAML file is the source of truth and the viewer is cloud-hosted, round-trip sync is complex. v1.0 should treat the hosted viewer as one-way upload, not two-way sync (avoid the Google Docs model for now).
- **REST API enables non-MCP agents:** CrewAI, LangChain, and other agent frameworks may not support MCP. The REST API in v1.0 makes the tool accessible to those ecosystems without waiting for MCP adoption.

---

## MVP Definition

This is a subsequent milestone context — the engine has shipped v0.2.0. "MVP" here means what v0.3 must ship to deliver its stated goal ("never need to say we can't render that").

### v0.3 Must Ship

- [ ] **Code syntax highlighting** — The single biggest gap vs. reveal.js/Marp. Developer credibility depends on this. Every demo deck has code.
- [ ] **Mermaid.js diagram support** — Developers use Mermaid in READMEs; they expect it in slides.
- [ ] **Video embed** — YouTube/Vimeo iframe embed is expected in any media-capable tool.
- [ ] **Slide fragments / progressive builds** — Needed for teaching decks, the #1 developer use case.
- [ ] **Finish editable PPTX** — Image-based PPTX is a partial solution; native shapes let people edit post-generation.

### v0.3 Add If Time Permits

- [ ] **Google Maps embed** — High novelty, low complexity (iframe embed), low risk.
- [ ] **PDF speaker notes** — Fills obvious gap; low complexity if using Playwright annotation layer.
- [ ] **Auto table of contents** — Nice for long technical decks.

### v0.3 Defer (Tempting But Wrong Scope)

- [ ] **Plugin system** — v0.4. Don't mix canvas polish with architecture changes.
- [ ] **LLM tools** — v0.5. Rich media must exist before AI generation is reliable.
- [ ] **Custom CSS per slide** — Low value, high maintenance surface.

---

## Feature Prioritization Matrix

### v0.3 Scope (Rich Media)

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Code syntax highlighting | HIGH (all devs) | LOW (Prism.js drop-in) | P1 |
| Slide fragments / progressive builds | HIGH (all users) | MEDIUM (JS state machine per slide) | P1 |
| Mermaid.js diagrams | HIGH (developers) | MEDIUM (async render, export static) | P1 |
| Video embed | MEDIUM (general users) | LOW (iframe + export thumbnail) | P1 |
| Finish editable PPTX | MEDIUM (general users) | HIGH (per-layout native renderers) | P2 |
| PDF speaker notes | MEDIUM (presenters) | MEDIUM (Playwright annotations) | P2 |
| Google Maps embed | LOW-MEDIUM (niche) | LOW (iframe + Static Maps API fallback) | P2 |
| Custom CSS per slide | LOW | LOW | P3 |
| Auto TOC slide | LOW | LOW | P3 |

### v0.4 Scope (Plugin Ecosystem)

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Layout plugin system | HIGH (ecosystem) | HIGH (entry points, schema merging) | P1 |
| Data source plugins | HIGH (data teams) | HIGH (async resolvers, credential management) | P1 |
| Theme plugin system | MEDIUM (design teams) | MEDIUM (CSS var conventions) | P2 |
| Plugin registry/CLI | MEDIUM (discoverability) | MEDIUM (JSON registry + CLI) | P2 |
| Template inheritance | LOW | MEDIUM | P3 |

### v0.5 Scope (LLM Integration)

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Structured output schemas per layout | HIGH (AI reliability) | MEDIUM (JSON Schema already in use) | P1 |
| generate_presentation(prompt) MCP tool | HIGH (AI agents) | HIGH (orchestration logic) | P1 |
| Content density optimizer | HIGH (agents can't see output) | MEDIUM (extend analyzer) | P1 |
| Slide suggestion engine | MEDIUM (creative assist) | HIGH (requires LLM calls) | P2 |
| Multi-agent workflow docs + contracts | MEDIUM (ecosystem) | LOW (documentation) | P2 |
| Accessibility checker | MEDIUM (compliance) | MEDIUM (ARIA audit) | P2 |

### v1.0 Scope (Platform)

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Hosted web viewer | HIGH (sharing) | HIGH (infra: storage, CDN, auth) | P1 |
| Embed codes | HIGH (distribution) | LOW (iframe snippet generator) | P1 |
| REST API | HIGH (non-MCP agents) | MEDIUM (FastAPI wrapper) | P1 |
| Presentation analytics | MEDIUM (presenters) | MEDIUM (event tracking) | P2 |
| Template marketplace | MEDIUM (discoverability) | MEDIUM (browse/install UI) | P2 |
| Real-time collaboration | LOW-MEDIUM (validate first) | HIGH (WebSocket + conflict resolution) | P3 |

---

## Competitor Feature Analysis

| Feature | reveal.js | Marp | Slidev | Gamma | Beautiful.ai | This Engine |
|---------|-----------|------|--------|-------|--------------|-------------|
| Code highlighting | YES (Highlight.js) | YES (Shiki) | YES (Shiki) | Basic | Basic | NOT YET |
| Diagram support | YES (Mermaid plugin) | LIMITED | YES (Mermaid) | NO | NO | PLANNED v0.3 |
| Structured data model | NO | NO | NO | Proprietary | Proprietary | YES (YAML+JSON) |
| MCP server | NO | NO | NO | NO | NO | YES |
| AI generation | NO | NO | NO | YES (SaaS) | YES (SaaS) | PLANNED v0.5 |
| Plugin system | YES (plugins) | LIMITED | YES (Vite plugins) | NO | NO | PLANNED v0.4 |
| PDF export | YES | YES | YES | YES | YES | YES |
| PPTX export | NO (plugin only) | YES | YES | YES | YES | YES (partial native) |
| Speaker notes | YES | YES | YES | YES | YES | YES |
| Fragments/builds | YES | LIMITED | YES | YES | YES | PLANNED v0.3 |
| Shareable URL | NO (self-host only) | NO | NO | YES | YES | PLANNED v1.0 |
| Analytics | NO | NO | NO | YES | YES | PLANNED v1.0 |
| Open source | YES | YES | YES | NO | NO | YES |
| Data source plugins | NO | NO | NO | Integrations | Integrations | PLANNED v0.4 |
| Editable PPTX | NO | Partial | YES | YES | YES | Partial (completing) |
| Video embed | YES | NO | YES | YES | YES | PLANNED v0.3 |

**Key insight:** This engine already beats every open-source competitor on AI-agent features (structured data, MCP). The gap is table-stakes developer features (code highlighting, fragments, diagrams) — which reveal.js, Marp, and Slidev have all shipped. These must close in v0.3 or developer credibility suffers.

---

## Sources

- Training data through August 2025 covering reveal.js 4.x, Marp 3.x, Slidev (June 2025), Gamma, Beautiful.ai, Tome
- Project context: `.planning/PROJECT.md` and `docs/plans/2026-03-05-roadmap-design.md`
- Codebase analysis: `pf/` source, `templates/`, `CLAUDE.md`, `docs/plans/`
- Confidence note: Web tools unavailable during this research session. Competitor feature tables reflect training data. Verify current Gamma/Beautiful.ai feature sets when web access is restored.

---

*Feature research for: Presentation engine / AI-native slide generator (v0.3 through v1.0)*
*Researched: 2026-03-05*
