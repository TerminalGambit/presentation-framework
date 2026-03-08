# Feature Research — Visual Editor (v0.3)

**Domain:** Visual web editor for a code-based presentation framework
**Researched:** 2026-03-08
**Confidence:** MEDIUM-HIGH (ecosystem surveyed via web search + official docs; UX patterns verified against Slidev, Marp, Gamma, Beautiful.ai, Pitch, Canva, Google Slides, reveal.js/Slides.com)

---

## Context: What This Research Covers

This file covers only what the **Next.js + React visual editor** needs to provide. The Python build engine (PresentationBuilder, FastAPI platform, MCP server, CLI) is already shipped. The editor is a consumer of the engine's REST API — it does not replace or duplicate the build pipeline.

### The Editor's Job

The editor lets non-CLI users create and edit presentations through a browser UI. It bridges the gap between "run `pf build` in a terminal" and a full visual authoring experience, without abandoning the code-as-configuration model.

### Primary User Persona for this Editor

**Non-technical or CLI-averse user** who wants to create branded slide decks without writing YAML by hand. They are not the AI agent persona (MCP covers that) and not the hardcore developer persona (CLI covers that). They are the "general user" segment: marketers, PMs, consultants, and designers handed this tool.

---

## Competitor UX Research Findings

### Code-Based Tools with Live Editors

**Slidev** (developer-focused Markdown slides):
- Integrated side editor: split pane with Monaco editor on left, live slide preview on right
- Changes sync via Vite HMR — instantaneous (< 100ms perceived lag)
- Auto-saves as you type (debounced)
- Presenter mode at `/presenter` route: current slide, speaker notes, next-slide preview
- Quick overview grid for non-linear navigation
- Notes editor at `/notes-edit` for batch speaker notes editing
- **Key insight:** Developers accept raw code editing because the preview is truly instant

**Marp Web Editor** (Markdown-based):
- Two-pane: Markdown editor left, rendered slide preview right
- "Blazing-fast" preview — updates without blocking typing
- Export: HTML, PDF, PPTX from the UI
- No template gallery — start from blank or paste Markdown
- **Key insight:** Speed of preview is the make-or-break feature; if preview lags, users abandon

### Visual/AI-First Tools

**Gamma.app** (card-based AI generation):
- Cards not slides — content blocks that auto-reflow
- Creation flow: "Generate with AI" or "Use template" or "Paste content"
- Dashboard: recent projects grid, "New" CTA prominent
- Template library organized by category (sales, marketing, portfolio, etc.)
- Editing: click any card, type directly; slash `/` for media inserts
- Per-card AI edit vs. whole-presentation AI edit
- **Key insight:** Template gallery + onboarding path is the primary acquisition moment

**Beautiful.ai** (Smart Slides):
- 300+ Smart Slide templates — each is a layout variant, not a full deck
- As you add content, layout auto-adjusts (no manual nudging)
- "Say goodbye to blank slides" — always start from a template
- Brand themes applied across all slides automatically
- **Key insight:** Form-based editing ("fill in this template") beats free YAML entry for non-developers

**Pitch** (team presentations):
- 100+ templates by category: pitch decks, sales, UX, business
- Real-time collaboration as a core differentiator
- "Pitch rooms" for organizing decks + links + files
- Analytics: knows when viewers open decks, which slides they viewed
- **Key insight:** Project organization (deck management) is as important as editing

**Slides.com (reveal.js)** (graphical editor for code presentations):
- Full WYSIWYG editor built on top of reveal.js
- Visual block placement on fixed-size canvas
- Template gallery at creation time
- **Key insight:** Even code-first tools need a GUI for mass adoption

### Standard UX Patterns (cross-tool consensus)

1. **Left slide panel** — thumbnail strip of all slides, click to navigate, drag to reorder
2. **Center canvas** — primary editing area (1280x720 or scaled)
3. **Right properties panel** — context-sensitive controls for selected element/slide
4. **Top toolbar** — add slide, layout picker, undo/redo, export, theme
5. **Template gallery** — category grid of thumbnail cards, hover to preview, click to use
6. **Save state indicator** — "Saved just now" / "Saving..." with timestamp
7. **Keyboard shortcuts** — Ctrl+Z/Y (undo/redo), Delete (remove slide), arrow keys (navigate)
8. **Empty state** — clear CTA to create first deck or use template on first login

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features that any visual presentation editor must have. Missing these = product feels broken.

| Feature | Why Expected | Complexity | Pipeline Dependency |
|---------|--------------|------------|---------------------|
| Live slide preview | Core value of a visual editor; users expect to see what they'll get | MEDIUM | POST /api/build → iframe render |
| Slide thumbnail panel (left sidebar) | Every presentation tool has a slide strip; it's muscle memory | LOW | Render each slide as thumbnail |
| Add / delete / duplicate slides | Most basic editing operation | LOW | YAML mutation + rebuild |
| Drag-to-reorder slides | Standard since PowerPoint; users drag thumbnails in panel | MEDIUM | dnd-kit sortable + YAML reorder |
| Template gallery with categories | Non-developers always start from a template, not blank YAML | MEDIUM | Static JSON manifest of template files |
| Layout picker when adding a slide | Users need to choose: "title slide", "two-column", etc. | LOW | 16 layouts already in engine |
| Export from editor (HTML, PDF, PPTX) | Every editor has download/export | LOW | Call existing /api/build endpoint |
| Autosave with status indicator | "Saving..." / "Saved just now" — prevents anxiety about lost work | LOW | Debounce + localStorage or API |
| Undo/redo | Universal expectation; Ctrl+Z is muscle memory | HIGH | Command pattern on YAML state |
| Keyboard navigation between slides | Arrow keys, Page Up/Down | LOW | Standard browser events |
| Theme controls (colors, fonts) | Users expect branding controls without editing YAML | LOW | Form inputs → theme section of YAML |
| Presentation management dashboard | "My presentations" grid — where you manage multiple decks | MEDIUM | IndexedDB or API storage |
| Error display for build failures | When YAML is invalid, user must know what's wrong | LOW | Map /api/validate errors to UI |
| Export download (zip/file) | Users need to get their output as a file | LOW | Wrap existing export endpoints |

### Differentiators (Competitive Advantage)

Features that set this editor apart, aligned with the engine's core value proposition.

| Feature | Value Proposition | Complexity | Pipeline Dependency |
|---------|-------------------|------------|---------------------|
| Side-by-side YAML + live preview | Developers and power users want raw code access; the "escape hatch" that code-based tools provide | MEDIUM | Monaco editor + debounced POST /api/build |
| Overflow warnings surfaced in UI | Engine already detects overflow; editor surfaces it as visual indicators on thumbnails | LOW | Already in /api/build response `warnings[]` |
| Contrast warnings surfaced in UI | WCAG checker already runs; editor surfaces them as badge warnings | LOW | Already in /api/build response `contrast_warnings[]` |
| Form-based slide editing | Structured form fields for each layout type (e.g., "left column cards" as a list input) — no YAML needed | HIGH | Maps to each layout's data schema |
| Layout-aware field forms | Different forms per layout type; form generates correct YAML | HIGH | Requires per-layout schema mapping |
| JSON metrics editor | Separate editor panel for metrics.json — shows which metrics are used | MEDIUM | Companion to YAML editor |
| Build warnings surfaced as slide badges | Red/yellow badge on slide thumbnails when overflow or contrast issue detected | LOW | Already in API response |
| Presenter mode preview | View the presentation in presenter mode (speaker notes + slide) from the editor | LOW | Reuse existing present.html |
| Template preview before use | Hover or click to see a rendered preview of a template before selecting it | MEDIUM | Pre-built HTML previews |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Full WYSIWYG drag-and-drop on canvas | "I want to move elements freely like PowerPoint" | Destroys the code-as-configuration model that enables AI generation, version control, and idempotent builds; would require reimplementing the render engine in React | Keep fixed layouts; let users pick a layout and fill content via forms |
| Real-time collaborative editing | "Like Google Docs for slides" | Operational transformation on YAML is extremely complex; merge conflicts in structured YAML are non-trivial; high operational cost | WebSocket presenter sync already exists for viewing; defer OT editing to v2+ |
| Per-element custom positioning | "Move this text box 14px to the right" | Breaks layout system; produces unmaintainable YAML; defeats responsive design | Trust the layout engine; form-based editing constrains to valid states |
| Built-in AI content writing | "Write my slide content for me" | Content authoring quality is unbounded scope; requires LLM API key management; support cost is high | Leverage existing MCP tools and LLM schemas — let AI agents fill the YAML, editor renders it |
| Offline-first PWA with sync | "I want to edit without internet" | Service worker + sync architecture is a 3-month scope; conflicts with server-side build pipeline | Save to localStorage for drafts; sync on reconnect is sufficient |
| Version history / git integration | "Show me the diff from last week" | Git integration from a web app is a complex security surface; version history requires storage infrastructure | Autosave to localStorage; "export as YAML" gives users git-ready files they manage themselves |
| Custom slide dimensions | "I need 16:10 instead of 16:9" | Fixed 1280x720px is a core engine constraint; all layouts are designed for this aspect ratio | Document the fixed size; it simplifies the layout engine and matches most display hardware |

---

## Feature Dependencies

```
Project Dashboard
    └──requires──> Presentation storage (IndexedDB or API)
    └──enables──> Template gallery "New from template" flow
    └──enables──> Deck list / recent decks

Template Gallery
    └──requires──> Static template manifest (JSON)
    └──requires──> Pre-built template YAML files
    └──enables──> "Use template" → copies YAML into editor

YAML + Live Preview Editor
    └──requires──> POST /api/build endpoint (FastAPI, already exists)
    └──requires──> Monaco editor (React wrapper)
    └──requires──> Debounce (300-500ms) on YAML change before build trigger
    └──requires──> iframe to render built present.html
    └──enables──> Form-based editing (form → generate YAML → same preview)

Form-Based Slide Editor
    └──requires──> YAML + Live Preview (same preview pipeline)
    └──requires──> Per-layout field schema mapping
    └──requires──> Each of the 16 layouts documented as a typed form
    └──conflicts──> Raw YAML editor (cannot sync two-way reliably without a YAML AST)
    └──NOTE──> Forms generate YAML; YAML is source of truth; forms don't parse YAML back

Drag-to-Reorder Slides
    └──requires──> Slide thumbnail panel
    └──requires──> dnd-kit/sortable
    └──requires──> YAML slides array mutation + rebuild trigger

Export (HTML/PDF/PPTX)
    └──requires──> A built deck_id from /api/build
    └──requires──> Trigger existing export flow
    └──enables──> Download button in editor toolbar

Build Warnings in UI
    └──requires──> /api/build response `warnings` + `contrast_warnings` fields
    └──already available: both fields exist in BuildResponse
    └──enables──> Slide thumbnail badges, warning panel

Undo/Redo
    └──requires──> Immutable YAML state history stack
    └──requires──> Command pattern or useReducer history
    └──NOTE──> Hardest feature; implement after basic editing works
```

### Dependency Notes

- **Form-based editing and raw YAML editing are in tension.** Forms generate YAML (one direction). If user switches to raw YAML and edits it, the form state must be rebuilt by parsing YAML — this is brittle. Resolution: make forms the primary path; raw YAML is an expert "escape hatch" that doesn't sync back to forms. State is: either in form mode or raw YAML mode, with a one-way "export to YAML" escape.
- **Live preview requires the FastAPI server to be running.** The Next.js editor is a client of the Python build API. In development, both run concurrently. In production, the FastAPI backend must be deployed alongside the Next.js frontend.
- **Template gallery is a lightweight static feature.** Templates are just pre-made YAML files. The "gallery" is a JSON manifest with category labels and thumbnail images. No server infrastructure needed beyond serving files.
- **Undo/redo is the highest-complexity table-stakes feature.** Every other editor has it; users expect Ctrl+Z to work. Implementation: maintain a stack of YAML snapshots (useReducer with history). Each edit pushes a snapshot; undo pops. Cap at 50 states to bound memory.
- **Drag-to-reorder needs dnd-kit/sortable** (not react-beautiful-dnd, which is deprecated). @dnd-kit is the current community standard as of 2025-2026 — accessible, performant, actively maintained.

---

## MVP Definition

### Launch With (Phase 1 — Project Dashboard + Template Gallery)

The minimum to make the editor useful to a non-technical user who has never touched YAML.

- [ ] **Presentation dashboard** — Grid of saved decks with name, last-modified, thumbnail. "New" button prominent. Empty state with clear CTA.
- [ ] **Template gallery** — Category-filtered grid of pre-built templates. Hover preview. "Use this template" copies YAML into a new deck.
- [ ] **Template content forms** — Guided forms to fill in template placeholders (title, subtitle, company name, etc.) without touching YAML.
- [ ] **Export from gallery** — After filling template form, export to HTML/PDF/PPTX directly. No need to enter full editor.

Why: Solves the largest user barrier ("I don't know how to write YAML") with the least implementation risk. Does not require building the full editor.

### Add After Validation (Phase 2 — Live YAML Editor)

Once the template gallery validates that users engage with the tool:

- [ ] **Split-pane YAML editor** — Monaco editor left, iframe preview right. Debounced build on change. Syntax highlighting for YAML.
- [ ] **JSON metrics editor** — Second tab in editor panel for metrics.json. Referenced paths highlighted.
- [ ] **Slide thumbnail panel** — Left sidebar showing all slides as thumbnails. Click to jump, drag to reorder.
- [ ] **Build warnings panel** — List of overflow and contrast warnings with slide number references.
- [ ] **Autosave + save state indicator** — "Saving..." spinner, "Saved 2s ago" timestamp.
- [ ] **Basic undo/redo** — Ctrl+Z/Y operating on YAML snapshot stack.
- [ ] **Export from editor** — Download HTML zip, trigger PDF/PPTX export via API.

Why: Power users and developers want raw YAML access. This phase makes the editor a viable replacement for the CLI for iterative editing.

### Future Consideration (Phase 3 — Visual Slide Editor)

After both previous phases have users, add form-based visual editing:

- [ ] **Form-based slide editing** — Right panel with typed fields for the current slide's layout. Forms generate YAML; they do not parse YAML back.
- [ ] **Layout picker** — Visual grid of 16 layout thumbnails when adding a new slide.
- [ ] **Theme controls UI** — Color pickers, font selector, style preset dropdown — all generating theme YAML.
- [ ] **Per-slide speaker notes input** — Text area below or beside slide, writing to `notes` field in YAML.
- [ ] **Slide transitions picker** — Dropdown per slide writing to `transition` field.

Why: This is the most complex phase (form ↔ YAML state management, per-layout schemas). Only worth building once earlier phases confirm the user persona exists and engages.

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority | Phase |
|---------|------------|---------------------|----------|-------|
| Project dashboard (deck list) | HIGH | LOW | P1 | 1 |
| Template gallery with categories | HIGH | LOW | P1 | 1 |
| Template content forms + export | HIGH | MEDIUM | P1 | 1 |
| YAML editor + live iframe preview | HIGH | MEDIUM | P1 | 2 |
| Slide thumbnail panel | HIGH | LOW | P1 | 2 |
| Autosave + save state indicator | HIGH | LOW | P1 | 2 |
| Export (HTML/PDF/PPTX) from editor | HIGH | LOW | P1 | 2 |
| Drag-to-reorder slides | MEDIUM | MEDIUM | P2 | 2 |
| Build warnings surfaced in UI | MEDIUM | LOW | P2 | 2 |
| Undo/redo (Ctrl+Z/Y) | HIGH | HIGH | P2 | 2 |
| JSON metrics editor | MEDIUM | LOW | P2 | 2 |
| Form-based slide editing (per layout) | HIGH | HIGH | P2 | 3 |
| Layout picker (16 layouts visual) | HIGH | MEDIUM | P2 | 3 |
| Theme controls UI | MEDIUM | MEDIUM | P2 | 3 |
| Speaker notes input | LOW | LOW | P3 | 3 |
| Slide transitions picker | LOW | LOW | P3 | 3 |
| Presenter mode preview link | LOW | LOW | P3 | 3 |

**Priority key:**
- P1: Must have for phase launch
- P2: Should have, add when possible in same phase
- P3: Nice to have, future consideration

---

## Competitor Feature Analysis

| Feature | Slidev | Marp Web | Gamma | Beautiful.ai | Pitch | This Editor |
|---------|--------|----------|-------|--------------|-------|-------------|
| Live YAML/Markdown editor | YES (Monaco) | YES | NO | NO | NO | YES (Phase 2) |
| Live preview (instant) | YES (HMR) | YES | YES | YES | YES | YES (debounced build) |
| Template gallery | Themes only | NO | YES | YES (300+) | YES (100+) | YES (Phase 1) |
| Form-based editing | NO | NO | Partial (cards) | YES (Smart Slides) | Partial | YES (Phase 3) |
| Drag-to-reorder slides | NO | NO | YES | YES | YES | YES (Phase 2) |
| Project dashboard | NO | NO | YES | YES | YES | YES (Phase 1) |
| Export from editor | YES | YES | YES | YES | YES | YES (Phase 1+2) |
| Build warnings in UI | NO | NO | NO | NO | NO | YES (unique to this engine) |
| Undo/redo | YES (editor) | YES | YES | YES | YES | YES (Phase 2) |
| YAML as source of truth | YES | YES | NO | NO | NO | YES (model preserved) |
| Open source | YES | YES | NO | NO | NO | YES |

**Key insight:** Slidev and Marp prove that a code editor with fast live preview is viable and valued by developers. Gamma and Beautiful.ai prove that form-based templates are the non-developer entry point. This editor can serve both: Phase 1-2 serves the template/export use case; Phase 3 adds form-based editing without abandoning YAML.

---

## Implementation Notes for the Python Engine Integration

The editor is a REST client of the existing FastAPI platform. Key integration points:

| Editor Action | API Endpoint | Notes |
|--------------|--------------|-------|
| Build/preview | `POST /api/build` (multipart: config + metrics) | Returns `deck_id`, `url`, `warnings`, `contrast_warnings` |
| Validate YAML | `POST /api/validate` | Returns `{valid, errors[]}` — use for inline editor validation |
| Load preview | `GET /d/{deck_id}/present.html` in iframe | iframe src set after successful build |
| Export HTML | `GET /d/{deck_id}/present.html` + zip download | Download the entire slides directory |
| Export PDF | Trigger `pf pdf` via API or subprocess | May need new endpoint |
| Export PPTX | Trigger `pf pptx` via API or subprocess | May need new endpoint |
| Embed code | `GET /api/decks/{deck_id}/embed` | Returns iframe HTML snippet |

**CORS is already configured with `allow_origins=["*"]`** in `pf_platform/api.py` — the Next.js editor can call the FastAPI backend from any origin without additional CORS work.

**Build is synchronous and runs in a thread pool** (`run_in_executor`) in the FastAPI worker — the editor should show a loading state for 1-3 seconds during build. The preview iframe should not refresh until the build completes.

**Rate limits are already set:** `/api/build` is limited to 10/minute per IP. For the editor's debounce-triggered builds, this is sufficient for normal editing pace (one build every 500ms max = 120/minute would exceed the limit, so the editor must debounce to at most one build per 6 seconds for a single user — or the rate limit needs adjustment for editor use).

**Rate limit is a blocker for live preview UX.** 10/minute = one build every 6 seconds. This is too slow for a "type and see" experience. The rate limit should be raised (or removed) for authenticated editor sessions. This is a dependency the Phase 2 roadmap must address.

---

## Sources

- [Slidev UI Guide](https://sli.dev/guide/ui) — navigation controls, presenter mode, integrated editor
- [Slidev Integrated Editor](https://sli.dev/features/side-editor) — side editor feature
- [Marp Discussion: marp-server live editor](https://github.com/orgs/marp-team/discussions/581) — two-pane live preview
- [Gamma Help Center: Create new presentation](https://help.gamma.app/en/articles/7838093-how-do-i-create-a-new-presentation-document-or-webpage-in-gamma) — creation flow
- [Beautiful.ai Smart Slides](https://www.beautiful.ai/smart-slides) — auto-layout UX
- [Pitch](https://pitch.com/) — template gallery, team presentations
- [dnd-kit Sortable](https://docs.dndkit.com/presets/sortable) — drag-to-reorder implementation
- [@dnd-kit GitHub](https://github.com/clauderic/dnd-kit) — modern drag-and-drop toolkit for React
- [GitLab Pajamas: Saving and feedback](https://design.gitlab.com/patterns/saving-and-feedback/) — autosave status patterns
- [Autosave UX pattern](https://ui-patterns.com/patterns/autosave) — save state indicators
- [monaco-yaml](https://github.com/remcohaszing/monaco-yaml) — YAML language support for Monaco Editor
- [Baymard: Secondary hover information](https://baymard.com/blog/secondary-hover-information) — thumbnail hover preview patterns
- `pf_platform/api.py` — existing REST API endpoints and rate limits
- `pf_platform/worker.py` — build pipeline integration point
- `.planning/PROJECT.md` — milestone requirements and constraints

---

*Feature research for: Visual editor web app (v0.3 milestone) for presentation-framework*
*Researched: 2026-03-08*
