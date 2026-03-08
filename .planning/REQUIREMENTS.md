# Requirements: Presentation Framework

**Defined:** 2026-03-08
**Core Value:** AI agents and humans can generate high-quality, branded presentations from structured data with a single command or tool call — now with a visual editor for non-CLI users.

## v0.3 Requirements

Requirements for the Visual Editor milestone. Each maps to roadmap phases.

### Infrastructure

- [ ] **INFRA-01**: User can launch the editor with `pf editor` command, which starts both Python and Next.js servers and opens the browser
- [ ] **INFRA-02**: Editor proxies API calls to FastAPI backend via Next.js rewrites (no CORS issues)
- [ ] **INFRA-03**: Editor displays iframe preview of real Python-built slide HTML
- [ ] **INFRA-04**: Local editor mode has no rate limit on build API calls

### Dashboard

- [ ] **DASH-01**: User can view all presentations in a grid dashboard with thumbnails
- [ ] **DASH-02**: User can create a new presentation from the dashboard
- [ ] **DASH-03**: User can delete a presentation from the dashboard
- [ ] **DASH-04**: User can open a presentation to edit from the dashboard

### Templates

- [ ] **TMPL-01**: User can browse pre-built templates organized by category
- [ ] **TMPL-02**: User can preview a template before selecting it
- [ ] **TMPL-03**: User can create a new presentation from a selected template
- [ ] **TMPL-04**: User can export a presentation to HTML from the editor
- [ ] **TMPL-05**: User can export a presentation to PDF from the editor
- [ ] **TMPL-06**: User can export a presentation to PPTX from the editor

### Editor

- [ ] **EDIT-01**: User can edit presentation YAML in a CodeMirror editor with syntax highlighting
- [ ] **EDIT-02**: User can see a live slide preview that updates as YAML changes
- [ ] **EDIT-03**: User can see slide thumbnails in a sidebar panel
- [ ] **EDIT-04**: User can add, delete, and duplicate slides from the sidebar
- [ ] **EDIT-05**: User can reorder slides via drag-and-drop
- [ ] **EDIT-06**: User can undo and redo changes with Ctrl+Z/Y
- [ ] **EDIT-07**: Editor auto-saves changes with a visible status indicator
- [ ] **EDIT-08**: User can edit metrics.json in a companion JSON editor pane
- [ ] **EDIT-09**: User can see build warnings and errors in the editor UI

### Visual Form Editor

- [ ] **FORM-01**: User can edit slide content through layout-specific form fields
- [ ] **FORM-02**: User can select a layout from a visual grid when adding a slide
- [ ] **FORM-03**: Form changes generate valid YAML without exposing syntax to user
- [ ] **FORM-04**: User can switch between form mode and YAML mode

### Theme Controls

- [ ] **THEME-01**: User can change primary and accent colors via color pickers
- [ ] **THEME-02**: User can select heading, subheading, and body fonts
- [ ] **THEME-03**: User can choose a style preset (modern/minimal/bold)

## Future Requirements

Deferred to v0.4+ milestone. Tracked but not in current roadmap.

### Collaboration

- **COLLAB-01**: Multiple users can edit a presentation simultaneously
- **COLLAB-02**: Users can leave comments on specific slides

### Platform

- **PLAT-01**: User can deploy the editor as a hosted web app with user accounts
- **PLAT-02**: User can share a presentation via URL from the editor
- **PLAT-03**: Presentations stored server-side with persistence

### Desktop Packaging

- **DESK-01**: Editor available as a downloadable desktop app (Tauri v2)
- **DESK-02**: Desktop app works fully offline

### AI Integration

- **AI-01**: User can generate slide content from a text prompt within the editor
- **AI-02**: User can get layout suggestions based on content

## Out of Scope

| Feature | Reason |
|---------|--------|
| Full WYSIWYG drag-and-drop element positioning | Destroys code-as-configuration model; incompatible with YAML source of truth |
| Real-time collaborative editing | OT on YAML is non-trivial; defer to v0.4+ after single-user is solid |
| Built-in AI content writing | MCP tools handle agent path; in-editor LLM is unbounded scope |
| Git integration / version history | Users manage YAML files in their own git repos |
| Custom slide dimensions | Fixed 1280x720 is a core engine constraint |
| Mobile responsive editor | Desktop-first; responsive deferred to hosted web milestone |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| INFRA-01 | — | Pending |
| INFRA-02 | — | Pending |
| INFRA-03 | — | Pending |
| INFRA-04 | — | Pending |
| DASH-01 | — | Pending |
| DASH-02 | — | Pending |
| DASH-03 | — | Pending |
| DASH-04 | — | Pending |
| TMPL-01 | — | Pending |
| TMPL-02 | — | Pending |
| TMPL-03 | — | Pending |
| TMPL-04 | — | Pending |
| TMPL-05 | — | Pending |
| TMPL-06 | — | Pending |
| EDIT-01 | — | Pending |
| EDIT-02 | — | Pending |
| EDIT-03 | — | Pending |
| EDIT-04 | — | Pending |
| EDIT-05 | — | Pending |
| EDIT-06 | — | Pending |
| EDIT-07 | — | Pending |
| EDIT-08 | — | Pending |
| EDIT-09 | — | Pending |
| FORM-01 | — | Pending |
| FORM-02 | — | Pending |
| FORM-03 | — | Pending |
| FORM-04 | — | Pending |
| THEME-01 | — | Pending |
| THEME-02 | — | Pending |
| THEME-03 | — | Pending |

**Coverage:**
- v0.3 requirements: 28 total
- Mapped to phases: 0
- Unmapped: 28

---
*Requirements defined: 2026-03-08*
*Last updated: 2026-03-08 after initial definition*
