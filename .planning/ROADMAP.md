# Roadmap: Presentation Framework

## Milestones

- ✅ **v0.2 — v1.0 Feature Complete** — Phases 1-4 (shipped 2026-03-07)
- 🚧 **v0.3 — Visual Editor** — Phases 5-8 (in progress)

## Phases

<details>
<summary>✅ v0.2 — v1.0 Feature Complete (Phases 1-4) — SHIPPED 2026-03-07</summary>

- [x] Phase 1: Rich Media + Export Polish (7/7 plans) — completed 2026-03-06
- [x] Phase 2: Plugin Ecosystem (5/5 plans) — completed 2026-03-06
- [x] Phase 3: LLM Integration (5/5 plans) — completed 2026-03-06
- [x] Phase 4: Hosted Platform (4/4 plans) — completed 2026-03-07

Full details: .planning/milestones/v0.2-ROADMAP.md

</details>

### 🚧 v0.3 — Visual Editor (In Progress)

**Milestone Goal:** Build a Next.js + React desktop-first application that gives non-CLI users a visual interface for creating, editing, and exporting presentations — without writing YAML by hand.

- [ ] **Phase 5: Editor Infrastructure** — Next.js app scaffold, `pf editor` CLI command, API proxy, iframe preview, rate limit fix
- [ ] **Phase 6: Dashboard + Template Gallery** — Presentation grid dashboard, template browsing, create from template, export from gallery
- [ ] **Phase 7: YAML Editor + Slide Management** — Live YAML/JSON editor with iframe preview, slide thumbnail panel, undo/redo, autosave
- [ ] **Phase 8: Visual Form Editor + Theme Controls** — Layout-specific form fields, layout picker, form-to-YAML serialization, theme UI

## Phase Details

### Phase 5: Editor Infrastructure
**Goal**: Users can launch a working browser-based editor with a real slide preview — all API calls proxied from Next.js to FastAPI with no CORS friction
**Depends on**: Phase 4 (FastAPI platform with `/api/build` and `/api/projects/*` endpoints)
**Requirements**: INFRA-01, INFRA-02, INFRA-03, INFRA-04
**Success Criteria** (what must be TRUE):
  1. User runs `pf editor` and a browser window opens showing the editor app
  2. The editor app shows a live slide preview that renders actual Python-built HTML in an iframe — no React slide re-implementation
  3. API calls from the browser never hit CORS errors — all proxied through Next.js rewrites to FastAPI
  4. Local editor mode has no rate limit — build API accepts unlimited calls from the local editor session
**Plans**: TBD

### Phase 6: Dashboard + Template Gallery
**Goal**: Users can browse their presentations, create new ones from templates, and export without writing any YAML
**Depends on**: Phase 5
**Requirements**: DASH-01, DASH-02, DASH-03, DASH-04, TMPL-01, TMPL-02, TMPL-03, TMPL-04, TMPL-05, TMPL-06
**Success Criteria** (what must be TRUE):
  1. User sees a grid dashboard of all their presentations with thumbnail previews
  2. User can create a new presentation, delete one, and open one to edit — all from the dashboard
  3. User can browse templates organized by category and preview a template before selecting it
  4. User can create a new presentation from a selected template (presentation file written to disk)
  5. User can export a presentation to HTML, PDF, and PPTX directly from the editor interface
**Plans**: TBD

### Phase 7: YAML Editor + Slide Management
**Goal**: Users can edit presentation YAML with live preview feedback and manage slides in a visual panel — without leaving the browser
**Depends on**: Phase 6
**Requirements**: EDIT-01, EDIT-02, EDIT-03, EDIT-04, EDIT-05, EDIT-06, EDIT-07, EDIT-08, EDIT-09
**Success Criteria** (what must be TRUE):
  1. User edits YAML in a CodeMirror editor with syntax highlighting and sees the slide preview update in real time
  2. User sees slide thumbnails in a sidebar and can add, delete, and duplicate slides from it
  3. User can reorder slides by dragging thumbnails in the sidebar
  4. User can undo and redo YAML changes with Ctrl+Z/Ctrl+Y
  5. Editor auto-saves changes with a visible status indicator, and build warnings/errors appear in the UI
**Plans**: TBD

### Phase 8: Visual Form Editor + Theme Controls
**Goal**: Users can edit slide content through layout-specific form fields and change theme appearance — never exposed to YAML syntax
**Depends on**: Phase 7
**Requirements**: FORM-01, FORM-02, FORM-03, FORM-04, THEME-01, THEME-02, THEME-03
**Success Criteria** (what must be TRUE):
  1. User can edit slide content via form fields that match the slide's layout — no raw YAML visible in form mode
  2. User can add a slide by choosing a layout from a visual grid picker
  3. Form changes update the slide preview — valid YAML is generated behind the scenes without syntax exposure
  4. User can switch between form mode and YAML mode for any slide
  5. User can change primary color, accent color, fonts, and style preset through UI controls that immediately update the preview
**Plans**: TBD

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Rich Media + Export Polish | v0.2 | 7/7 | Complete | 2026-03-06 |
| 2. Plugin Ecosystem | v0.2 | 5/5 | Complete | 2026-03-06 |
| 3. LLM Integration | v0.2 | 5/5 | Complete | 2026-03-06 |
| 4. Hosted Platform | v0.2 | 4/4 | Complete | 2026-03-07 |
| 5. Editor Infrastructure | v0.3 | 0/? | Not started | - |
| 6. Dashboard + Template Gallery | v0.3 | 0/? | Not started | - |
| 7. YAML Editor + Slide Management | v0.3 | 0/? | Not started | - |
| 8. Visual Form Editor + Theme Controls | v0.3 | 0/? | Not started | - |
