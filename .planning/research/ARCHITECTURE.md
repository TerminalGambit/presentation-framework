# Architecture Research

**Domain:** Next.js visual editor integrating with existing Python presentation build engine
**Researched:** 2026-03-08
**Confidence:** HIGH (existing Python codebase analyzed directly; Next.js patterns from official docs + verified sources; integration patterns from current Next.js 16.x docs)

---

## Context: What Already Exists (Must Integrate With)

This is a **subsequent milestone** architecture document. The v0.3 Visual Editor adds a Next.js frontend to an existing Python engine. Before designing anything, the integration constraints:

| Existing Component | Location | Role for Editor |
|-------------------|----------|-----------------|
| `PresentationBuilder` | `pf/builder.py` | Core build engine — editor triggers this |
| FastAPI platform | `pf_platform/api.py` | REST API the editor calls |
| `/api/build` (POST) | FastAPI | Accepts `config` + `metrics` file uploads → returns `deck_id`, `url`, warnings |
| `/api/validate` (POST) | FastAPI | Validates YAML config → returns errors list |
| `/d/{deck_id}/present.html` | FastAPI static | Built slide output — embed as iframe in editor preview |
| `/ws/{deck_id}` | FastAPI WebSocket | Presenter sync — editor may also use for live updates |
| `pf/schema.json` | JSON Schema | Validates `presentation.yaml` — can be used client-side too |
| YAML + JSON data model | Files | Source of truth — editor reads/writes these |

**Key architectural constraint from PROJECT.md:** "Presentations-as-code is the core philosophy." The editor is a GUI layer over the YAML data model — it cannot replace or bypass it.

---

## System Overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          Next.js Editor (v0.3)                            │
│                                                                            │
│  ┌─────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐  │
│  │  Project        │  │  Template        │  │  Slide Editor             │  │
│  │  Dashboard      │  │  Gallery         │  │  (YAML + Visual)          │  │
│  │  /dashboard     │  │  /templates      │  │  /editor/[id]             │  │
│  └────────┬────────┘  └────────┬─────────┘  └────────────┬─────────────┘  │
│           │                   │                           │                │
│  ┌────────┴───────────────────┴───────────────────────────┴─────────────┐  │
│  │                  Zustand Store (client state)                          │  │
│  │  currentProject · slides[] · activeSlide · buildStatus · warnings[]   │  │
│  └───────────────────────────────────┬────────────────────────────────────┘  │
│                                      │                                    │
│  ┌───────────────────────────────────┴────────────────────────────────────┐  │
│  │            Next.js Route Handlers  (app/api/*)                         │  │
│  │  Proxy layer: auth checks, request transformation, CORS normalization  │  │
│  └───────────────────────────────────┬────────────────────────────────────┘  │
└──────────────────────────────────────┼────────────────────────────────────────┘
                                       │ HTTP / multipart form
                                       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    Existing FastAPI Platform (Python)                      │
│                                                                            │
│  POST /api/build     POST /api/validate     GET /api/decks/{id}/embed     │
│  DELETE /api/decks/{id}                     WS /ws/{deck_id}              │
│                                                                            │
│  pf_platform/ (existing — no changes needed for v0.3)                     │
└──────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         Core Python Engine                                 │
│  PresentationBuilder → Jinja2 → HTML slides (existing, unchanged)         │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Component Responsibilities

| Component | Responsibility | New vs Existing |
|-----------|----------------|-----------------|
| Next.js App (`editor/`) | Dashboard, gallery, editor UI | NEW |
| Zustand store | Client-side presentation state | NEW |
| Route Handlers (`app/api/`) | Proxy/transform calls to FastAPI | NEW |
| Monaco Editor | YAML/JSON code editing | NEW (library) |
| Preview iframe | Renders `present.html` built by Python | EXISTING output, new embedding |
| FastAPI platform | Build, validate, serve slides | EXISTING (no changes) |
| PresentationBuilder | Core Jinja2 render pipeline | EXISTING (no changes) |

---

## Recommended Project Structure

```
presentation-framework/
├── pf/                             # Existing Python core (unchanged)
├── pf_platform/                    # Existing FastAPI platform (unchanged for v0.3)
├── templates/                      # Existing Jinja2 templates (unchanged)
│
└── editor/                         # NEW — Next.js visual editor
    ├── app/                        # App Router root
    │   ├── layout.tsx              # Root layout (font, global providers)
    │   ├── page.tsx                # Redirects → /dashboard
    │   │
    │   ├── dashboard/              # Project list + management
    │   │   └── page.tsx
    │   │
    │   ├── templates/              # Template gallery
    │   │   └── page.tsx
    │   │
    │   ├── editor/                 # Slide editor (main feature)
    │   │   └── [projectId]/
    │   │       ├── page.tsx        # Editor shell (layout split)
    │   │       └── layout.tsx      # Editor-specific layout (no nav chrome)
    │   │
    │   └── api/                    # Next.js Route Handlers (proxy layer)
    │       ├── build/
    │       │   └── route.ts        # POST → FastAPI /api/build
    │       ├── validate/
    │       │   └── route.ts        # POST → FastAPI /api/validate
    │       └── decks/
    │           └── [deckId]/
    │               └── route.ts    # DELETE → FastAPI /api/decks/{id}
    │
    ├── components/                 # Shared React components
    │   ├── ui/                     # Primitives (Button, Input, Badge, etc.)
    │   ├── editor/                 # Editor-specific components
    │   │   ├── SlideList.tsx       # Slide thumbnail strip (dnd-kit reordering)
    │   │   ├── YamlEditor.tsx      # Monaco editor wrapper (YAML mode)
    │   │   ├── MetricsEditor.tsx   # Monaco editor wrapper (JSON mode)
    │   │   ├── PreviewPane.tsx     # iframe embedding present.html
    │   │   ├── SlideForm.tsx       # Form-based slide data editor
    │   │   ├── LayoutPicker.tsx    # Visual layout selector
    │   │   └── WarningBanner.tsx   # Build warnings display
    │   ├── dashboard/
    │   │   ├── ProjectCard.tsx     # Deck thumbnail card
    │   │   └── NewProjectDialog.tsx
    │   └── layout/
    │       ├── Sidebar.tsx
    │       └── TopBar.tsx
    │
    ├── lib/                        # Utilities, API clients, type definitions
    │   ├── api.ts                  # Typed client for Next.js Route Handlers
    │   ├── python-api.ts           # Direct FastAPI client (for server-side use)
    │   ├── types.ts                # Shared TypeScript types (Slide, Layout, etc.)
    │   ├── yaml-utils.ts           # YAML parse/serialize with js-yaml
    │   └── schema.ts               # Import pf/schema.json for client-side validation
    │
    ├── store/                      # Zustand stores
    │   ├── editor-store.ts         # Main editor state (slides, active slide, dirty flag)
    │   ├── build-store.ts          # Build status, warnings, deck IDs
    │   └── project-store.ts        # Project list, current project metadata
    │
    ├── hooks/                      # Custom React hooks
    │   ├── useBuild.ts             # Trigger build, poll status, return warnings
    │   ├── useAutoSave.ts          # Debounced save on store change
    │   └── usePreview.ts           # Manage preview iframe src updates
    │
    ├── public/                     # Static assets
    ├── package.json
    ├── next.config.ts              # rewrites for /preview/* → FastAPI /d/*
    └── tsconfig.json
```

### Structure Rationale

- `editor/` lives alongside (not inside) `pf/` — it is a separate Node.js project, not a Python module. The Python engine does not need to know about it.
- `app/api/` Route Handlers are a thin proxy layer, not a second backend. They handle CORS normalization, multipart→JSON transformation, and future auth injection without adding business logic.
- `store/` is split by concern (`editor-store`, `build-store`, `project-store`) — each store is independently subscribable, preventing unnecessary re-renders when only build status changes.
- `lib/api.ts` encapsulates all HTTP calls so components never call `fetch()` directly. This makes testing and API URL changes trivial.
- Co-locating editor-specific components in `components/editor/` prevents them from polluting the shared `components/ui/` layer.

---

## Architectural Patterns

### Pattern 1: Next.js rewrites for FastAPI Proxy (No Route Handler Needed for Slides)

**What:** Use `next.config.ts` rewrites to transparently proxy `/preview/*` paths to the FastAPI `/d/*` paths. Built slide HTML is served directly from Python with no Next.js hop.

**When to use:** For serving the built slide output (static files from FastAPI). Do not proxy through a Route Handler — that adds latency and a streaming body copy. Use Route Handlers only for build/validate API calls where you need to add headers or transform payloads.

**Configuration:**

```typescript
// editor/next.config.ts
const nextConfig = {
  async rewrites() {
    return [
      {
        // Proxy /preview/DECK_ID/* to FastAPI /d/DECK_ID/*
        source: '/preview/:deckId/:path*',
        destination: `${process.env.PYTHON_API_URL}/d/:deckId/:path*`,
      },
    ]
  },
}
```

**Trade-offs:** Rewrites are resolved in the Next.js edge layer, so they add minimal overhead. The slide HTML is served with FastAPI's CSP headers intact (`frame-ancestors *`). This avoids re-serving 1280x720 HTML through Node.js.

### Pattern 2: Route Handlers as a Typed API Layer for Build Calls

**What:** Next.js Route Handlers (`app/api/build/route.ts`) proxy build and validate calls to FastAPI. They handle multipart form encoding, add any future auth headers, and return typed JSON responses.

**When to use:** For POST calls that submit YAML + JSON files to FastAPI's `/api/build` and `/api/validate` endpoints. The editor sends JSON; the Route Handler re-packages it as multipart before forwarding.

**Example:**

```typescript
// editor/app/api/build/route.ts
export async function POST(request: Request) {
  const body = await request.json()
  // body: { config: string (YAML), metrics: string (JSON) }

  const formData = new FormData()
  formData.append('config', new Blob([body.config], { type: 'text/yaml' }), 'presentation.yaml')
  formData.append('metrics', new Blob([body.metrics], { type: 'application/json' }), 'metrics.json')

  const response = await fetch(`${process.env.PYTHON_API_URL}/api/build`, {
    method: 'POST',
    body: formData,
  })

  const data = await response.json()
  // data: { deck_id, url, slide_count, warnings[] }

  return Response.json(data, { status: response.status })
}
```

**Trade-offs:** One extra HTTP hop (Next.js → FastAPI). Acceptable because build calls are not latency-sensitive — a Jinja2 render takes ~200ms minimum. The benefit is CORS normalization and a stable internal API contract.

### Pattern 3: Iframe Preview with postMessage Coordination

**What:** The slide preview pane is an `<iframe>` pointing at `/preview/{deckId}/present.html`. The editor sends `postMessage` to navigate to the active slide; the iframe replies with navigation events.

**When to use:** For live preview. Do not re-implement slide rendering in React — the Python Jinja2 output IS the source of truth. Rendering it a second time in client JS would diverge and cause constant bugs.

**Flow:**

```
Editor triggers build
         │
         ▼
POST /api/build → returns deckId
         │
         ▼
PreviewPane sets <iframe src="/preview/{deckId}/present.html">
         │
         ▼
User selects slide N in SlideList
         │
         ▼
iframe.contentWindow.postMessage({ type: 'goto', slide: N }, '*')
         │
         ▼
present.html JS handler: window.addEventListener('message', handler)
```

**Key requirement:** The existing `present.html.j2` template needs one addition — a `window.addEventListener('message')` handler that accepts `{ type: 'goto', slide: N }` and calls the existing `goToSlide(n)` function. This is the only change needed to `pf/` for the preview integration (MEDIUM scope, backward-compatible).

**Trade-offs:** Build → preview cycle requires a full Python build (~200-500ms). For the YAML editor, this is fine — trigger on save, not on every keystroke. For the visual form editor, trigger on blur or explicit "Apply" button.

### Pattern 4: Zustand for Editor State (Not Redux, Not Context)

**What:** Zustand stores hold the presentation's runtime state in the editor: the current slides array, active slide index, raw YAML/JSON strings, build status, and warnings. State is split into three stores to minimize re-renders.

**When to use:** Zustand is the right choice here because:
- The editor state is moderately complex (slides array + nested slide data) but not enterprise-scale
- Zustand's selector-based subscriptions prevent the whole editor from re-rendering when only build status changes
- Zustand works without a Provider wrapper, which matters in App Router where Server/Client component boundaries are strict

**Do not use:**
- Redux Toolkit: adds boilerplate (slices, actions, reducers) for no benefit at this scale; Zustand delivers the same functionality with ~80% less code
- React Context: no built-in selector support means a slide data change re-renders the entire component tree including the Monaco editor, causing visible flicker

**Store shape:**

```typescript
// editor/store/editor-store.ts
import { create } from 'zustand'
import { immer } from 'zustand/middleware/immer'

interface Slide {
  id: string
  layout: string
  data: Record<string, unknown>
  notes?: string
}

interface EditorStore {
  slides: Slide[]
  activeSlideIndex: number
  rawYaml: string          // the full presentation.yaml text
  rawMetrics: string       // the metrics.json text
  isDirty: boolean         // unsaved changes flag

  setActiveSlide: (index: number) => void
  updateSlide: (index: number, data: Partial<Slide>) => void
  reorderSlides: (fromIndex: number, toIndex: number) => void
  setRawYaml: (yaml: string) => void
  setRawMetrics: (json: string) => void
}

export const useEditorStore = create<EditorStore>()(
  immer((set) => ({
    slides: [],
    activeSlideIndex: 0,
    rawYaml: '',
    rawMetrics: '{}',
    isDirty: false,

    setActiveSlide: (index) => set((s) => { s.activeSlideIndex = index }),
    updateSlide: (index, data) => set((s) => {
      Object.assign(s.slides[index], data)
      s.isDirty = true
    }),
    reorderSlides: (from, to) => set((s) => {
      const [slide] = s.slides.splice(from, 1)
      s.slides.splice(to, 0, slide)
      s.isDirty = true
    }),
    setRawYaml: (yaml) => set((s) => { s.rawYaml = yaml; s.isDirty = true }),
    setRawMetrics: (json) => set((s) => { s.rawMetrics = json; s.isDirty = true }),
  }))
)
```

**Trade-off of immer middleware:** Immer allows direct mutation syntax in store updates, which is safer for nested slide data than manual spread-and-replace patterns. Worth the 14KB addition.

### Pattern 5: Dual-Mode Editor (YAML Code View + Form View)

**What:** The editor exposes two views of the same data — a raw YAML/JSON code editor (Monaco) and a structured form editor. Both views read from and write to the same Zustand store. Switching modes re-serializes the current state.

**When to use:** This is the "presentations-as-code" philosophy made accessible. Power users and AI agents work in YAML; less technical users work in the form view. The key invariant: both views produce identical YAML output.

**Data flow:**

```
Form view (SlideForm)
   └─ user changes title field
         │
         ▼
   updateSlide(idx, { title: 'New title' })  → Zustand store
         │
         ├─► YAML view (Monaco): re-serialized from store.slides[]
         │
         └─► Preview: build triggered (debounced 1500ms after last change)
```

**YAML → Form sync:**

```
YAML view (Monaco)
   └─ user edits YAML
         │
         ▼
   parse YAML with js-yaml → setRawYaml() + update slides[]
         │
         ├─► Form view: populated from updated slides[]
         │
         └─► Preview: build triggered
```

**Sync failure handling:** When YAML parse fails (syntax error), the form view shows stale data with a warning badge. The YAML view shows the Monaco error gutter. The form never overwrites with invalid state.

### Pattern 6: Local-First File System via Python CLI Bridge (Not Browser File System API)

**What:** For local-first mode, the editor does not use the browser's File System Access API. Instead, it calls a local Python CLI endpoint to read and write files on disk.

**Why not the browser File System Access API:** The File System Access API requires user permission prompts for every directory and has inconsistent support. More importantly, the workflow is already CLI-based — users have a project directory with `presentation.yaml` and `metrics.json`. The cleanest integration is a local dev server mode where `pf serve --editor` starts both the FastAPI platform AND a file-access endpoint.

**Local mode architecture:**

```
pf serve --editor
  └─ starts FastAPI platform (existing, port 8000)
  └─ starts Next.js editor dev server (port 3000)
  └─ Next.js editor connects to FastAPI for build/validate
  └─ FastAPI adds /api/projects/* endpoints for file I/O:
       GET  /api/projects          → list project directories
       GET  /api/projects/{id}     → read presentation.yaml + metrics.json
       PUT  /api/projects/{id}     → write presentation.yaml + metrics.json
```

**This means:** The editor does not need to be a separate process for local use. The existing FastAPI platform gets three new file-access endpoints (scoped to the local directory), and `pf serve --editor` becomes the single launch command.

**Trade-off:** Adds 3 new routes to `pf_platform/api.py` (file listing, read, write). These are local-only (blocked in hosted mode by an env flag). Simpler than implementing browser File System API or Electron-style file access.

---

## Data Flow

### Build and Preview Flow

```
User edits YAML in Monaco (or form fields)
         │
         │ (debounced 1500ms)
         ▼
useBuild() hook fires
         │
         ▼
POST /api/build (Next.js Route Handler)
   → packages { config: yaml, metrics: json } → multipart form
   → forwards to FastAPI POST /api/build
         │
         ▼
FastAPI builds: PresentationBuilder → Jinja2 → HTML → /data/{deck_id}/slides/
Returns: { deck_id, url, slide_count, warnings[] }
         │
         ▼
build-store.ts updates: { deckId, warnings, status: 'success' }
         │
         ├─► WarningBanner re-renders with warnings list
         │
         └─► PreviewPane: iframe.src = `/preview/${deckId}/present.html`
                  (via next.config.ts rewrite → FastAPI /d/{deckId}/present.html)
```

### YAML ↔ Form State Sync

```
Zustand editor-store (source of truth)
   ├── slides: Slide[]         ← parsed representation
   └── rawYaml: string         ← serialized YAML (kept in sync)

YAML view writes:       rawYaml → parse → update slides[]
Form view writes:       updateSlide() → serialize → update rawYaml
Monaco displays:        rawYaml (controlled input)
Form displays:          slides[activeSlideIndex]
Preview receives:       rawYaml + rawMetrics → sent to build endpoint
```

### Project Save Flow (Local Mode)

```
User clicks Save (or auto-save triggers)
         │
         ▼
PUT /api/projects/{projectId}
   body: { config: rawYaml, metrics: rawMetrics }
         │
         ▼
FastAPI /api/projects/{id} handler writes files to disk:
   {project_dir}/presentation.yaml
   {project_dir}/metrics.json
         │
         ▼
editor-store: isDirty = false
```

---

## New vs Modified Components

### New Components (v0.3)

| Component | File | Description |
|-----------|------|-------------|
| Next.js editor app | `editor/` | Entire Next.js application |
| Monaco YAML editor | `components/editor/YamlEditor.tsx` | `@monaco-editor/react` with `monaco-yaml` YAML schema validation |
| Monaco JSON editor | `components/editor/MetricsEditor.tsx` | Monaco with JSON mode and schema validation |
| Preview pane | `components/editor/PreviewPane.tsx` | iframe wrapper + postMessage controller |
| Slide list | `components/editor/SlideList.tsx` | Thumbnail strip with `@dnd-kit/sortable` for drag reorder |
| Slide form | `components/editor/SlideForm.tsx` | Per-layout form fields (generated from layout type) |
| Layout picker | `components/editor/LayoutPicker.tsx` | Visual grid of layout options |
| Dashboard | `app/dashboard/page.tsx` | Project list, create/delete |
| Template gallery | `app/templates/page.tsx` | Pre-built templates with one-click import |
| Route Handlers | `app/api/build/route.ts` etc. | Thin proxy to FastAPI |
| Zustand stores | `store/*.ts` | Editor, build, project state |
| Build hook | `hooks/useBuild.ts` | Debounced build trigger + status |
| API client | `lib/api.ts` | Typed fetch wrappers |

### Existing Components Modified (v0.3)

| Component | File | Change | Scope |
|-----------|------|--------|-------|
| `present.html.j2` | `templates/present.html.j2` | Add `window.addEventListener('message')` handler for `{ type: 'goto', slide: N }` | Small — ~10 lines of JS added to existing handler block |
| `pf_platform/api.py` | Existing FastAPI app | Add 3 file-access routes: `GET /api/projects`, `GET/PUT /api/projects/{id}` | Medium — new route group, no changes to existing routes |
| `pf serve` CLI command | `pf/cli.py` | Add `--editor` flag to also launch Next.js dev server | Small — subprocess call to `npm run dev` in `editor/` |

### Existing Components Unchanged

- `pf/builder.py` — untouched
- `pf/analyzer.py` — untouched
- `pf_platform/storage.py` — untouched
- `pf_platform/sync.py` — untouched
- All existing `/api/build`, `/api/validate`, `/api/decks/*` routes — untouched

---

## Build Order (Progressive Feature Layers)

```
Layer 1: Infrastructure (no UI yet)
  ├── Scaffold Next.js app in editor/ (next@16, TypeScript, Tailwind)
  ├── Configure next.config.ts rewrites (/preview/* → FastAPI)
  ├── Implement lib/api.ts typed client
  ├── app/api/build/route.ts and app/api/validate/route.ts (Route Handler proxies)
  └── Verify round-trip: POST to Route Handler → FastAPI → deck_id returned

Layer 2: Preview Pane
  ├── Build PreviewPane.tsx (iframe wrapper)
  ├── Add postMessage listener to present.html.j2 (only pf/ change in this layer)
  ├── Wire PreviewPane to a hardcoded test deck_id
  └── Verify: slide navigation via postMessage from parent

Layer 3: YAML/JSON Editor
  ├── YamlEditor.tsx with @monaco-editor/react + monaco-yaml
  ├── MetricsEditor.tsx with JSON schema validation from pf/schema.json
  ├── Scaffold Zustand stores (editor-store, build-store)
  ├── useBuild hook with 1500ms debounce
  └── Wire: YAML change → build → preview updates

Layer 4: Project Dashboard + File I/O
  ├── Add /api/projects/* routes to pf_platform/api.py (local file read/write)
  ├── project-store.ts
  ├── Dashboard page (list, create, open)
  └── Auto-save with useAutoSave hook

Layer 5: Visual Slide Editor
  ├── SlideList.tsx with @dnd-kit/sortable (thumbnail strip + drag reorder)
  ├── LayoutPicker.tsx (visual layout grid)
  ├── SlideForm.tsx (per-layout form fields — start with two-column, title, stat-grid)
  ├── YAML ↔ Form bidirectional sync
  └── Slide add/delete/duplicate controls

Layer 6: Template Gallery + Export
  ├── Template definitions (static JSON, embedded in app)
  ├── Template gallery page with live preview thumbnails
  ├── One-click template import to editor
  └── Export buttons: HTML (serve present.html), PDF (POST /api/export/pdf if exists), PPTX
```

**Layer ordering rationale:**

- Layer 1 before everything: infrastructure and API contracts must be stable before UI is built on top. Route Handlers define the interface the rest of the app uses.
- Layer 2 (preview) before Layer 3 (YAML editor): establishing that the iframe preview works correctly confirms the core integration before adding editing complexity.
- Layer 3 (YAML editor) before Layer 5 (visual editor): the visual editor must produce valid YAML — it's a form layer on top of the YAML model. Building and testing the YAML path first means the visual editor can be verified against a known-good serialization.
- Layer 4 (file I/O) can be built in parallel with Layer 3, but dashboard UI depends on project listing being available.
- Layer 6 (templates + export) is last because it depends on the editor being functional to test template imports meaningfully.

---

## Integration Points

### Next.js → FastAPI Boundaries

| Boundary | Direction | Method | Notes |
|----------|-----------|--------|-------|
| Build trigger | Next.js → FastAPI | POST multipart form | Route Handler transforms JSON body → multipart |
| Validate | Next.js → FastAPI | POST multipart form | Same transformation pattern |
| Delete deck | Next.js → FastAPI | DELETE | Simple proxy, no transformation |
| Slide preview serving | Browser → FastAPI (via rewrite) | GET | next.config.ts rewrite, no Route Handler |
| WebSocket sync | Browser → FastAPI | WS | Direct connection, no Next.js hop |
| File read/write | Next.js → FastAPI | GET/PUT JSON | New endpoints in pf_platform/api.py |

### present.html ↔ Preview Pane Boundary

The only cross-origin concern is postMessage. The iframe's origin is `http://localhost:8000` (FastAPI) when Next.js runs on port 3000. The `postMessage` target must be `'*'` or the explicit FastAPI origin — use `'*'` in development and tighten in production.

```typescript
// editor/components/editor/PreviewPane.tsx
const goToSlide = (index: number) => {
  iframeRef.current?.contentWindow?.postMessage(
    { type: 'goto', slide: index },
    process.env.NEXT_PUBLIC_PYTHON_API_URL ?? '*'
  )
}
```

```javascript
// templates/present.html.j2 addition
window.addEventListener('message', (event) => {
  if (event.data?.type === 'goto' && typeof event.data.slide === 'number') {
    goToSlide(event.data.slide)  // existing function
  }
})
```

### State Synchronization: YAML Editor ↔ Visual Form

The critical invariant: at no point should the Zustand store hold both an updated `rawYaml` and stale `slides[]` (or vice versa). Use a single serialization function for YAML→store and store→YAML to ensure they're inverse operations.

```typescript
// lib/yaml-utils.ts
import YAML from 'js-yaml'

export function yamlToStore(raw: string): Slide[] {
  const config = YAML.load(raw) as PresentationConfig
  return config.slides ?? []
}

export function storeToYaml(slides: Slide[], theme: Theme): string {
  return YAML.dump({ theme, slides })
}
```

Mutations always go through one of two paths:
1. `setRawYaml(yaml)` → parse → update `slides[]`
2. `updateSlide(idx, data)` → update `slides[idx]` → re-serialize → update `rawYaml`

No component should update both independently.

---

## Anti-Patterns

### Anti-Pattern 1: Re-implementing Slide Rendering in React

**What people do:** Build a React component that takes slide data and renders a 1280x720 preview — mirroring the Python Jinja2 templates in JSX.

**Why it's wrong:** The Python templates are the source of truth. A JS mirror will immediately diverge as new layouts, Plotly charts, KaTeX math, and Mermaid diagrams are added. You now maintain two rendering implementations, and visual fidelity bugs become constant.

**Do this instead:** Embed `present.html` in an iframe. The Python output IS the preview. Accept the ~300ms build latency — it is not a real problem at the editing cadence users actually work at (save → review → adjust).

### Anti-Pattern 2: Calling FastAPI Directly from the Browser

**What people do:** Browser `fetch('http://localhost:8000/api/build', ...)` directly from React components.

**Why it's wrong:** CORS errors in production (FastAPI and Next.js on different origins/ports), hardcoded URLs in component code, no place to add auth headers or request transformation later.

**Do this instead:** All API calls go through `lib/api.ts`, which calls Next.js Route Handlers at `/api/*`. The Route Handlers proxy to FastAPI. Browser never knows FastAPI's URL.

### Anti-Pattern 3: Syncing YAML and Form State via useEffect

**What people do:** `useEffect(() => { setFormData(parseYaml(rawYaml)) }, [rawYaml])` — using effects to keep derived state in sync.

**Why it's wrong:** Creates timing issues (effect runs after render), stale closure bugs when multiple effects fire in sequence, and double-renders. React 18 strict mode runs effects twice in development, causing spurious builds.

**Do this instead:** Single source of truth in Zustand. Derived values (parsed slides from rawYaml) are computed in selectors, not synced via effects. Store update functions maintain invariants internally using Immer.

### Anti-Pattern 4: Storing the Deck ID in the URL Only

**What people do:** Put the current `deckId` in the URL (`/editor/[projectId]?deckId=abc123`) so the preview pane knows what to show.

**Why it's wrong:** Every build produces a new `deckId` (UUID from `store_deck()`). Updating the URL on every build causes browser history pollution, and the preview iframe loses scroll/slide position on navigation.

**Do this instead:** `deckId` lives in `build-store.ts`. The preview pane subscribes to it via Zustand. The URL only contains `projectId` (stable identifier for the project being edited).

---

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| Local-only (single user) | pf serve --editor; Next.js dev server; SQLite; file-based storage |
| Small team (shared hosted instance) | Deploy Next.js to Vercel/Railway; FastAPI on separate process; deck IDs are ephemeral |
| Multi-tenant hosted | Add user sessions to Next.js Route Handlers; FastAPI platform gets project ownership; deck storage moves to S3/R2 |

**First bottleneck:** Build latency. The Python build pipeline is synchronous. At ~300ms per build, debouncing to 1500ms after last edit means the preview lags by up to 1.8 seconds. This is acceptable for v0.3. If it becomes a problem, add a visual "building..." spinner in the PreviewPane and the UX feels responsive even if the latency is unchanged.

**Second bottleneck:** Template gallery thumbnails. Generating preview thumbnails for 20+ templates requires building each one. Use pre-built screenshot thumbnails (PNG) stored in the editor app's `public/` directory — do not build them on demand.

---

## Technology Decisions Summary

| Decision | Chosen | Rationale |
|----------|--------|-----------|
| State management | Zustand + Immer | Minimal boilerplate for moderate state complexity; selector subscriptions prevent unnecessary re-renders; works cleanly with App Router Server/Client boundaries |
| YAML/JSON editor | `@monaco-editor/react` + `monaco-yaml` | Industry-standard editor with YAML language server support, schema validation from `pf/schema.json`, no webpack config needed in Next.js |
| Drag-and-drop | `@dnd-kit/sortable` | Accessible, keyboard-navigable, works with React 18, no deprecated dependencies (react-beautiful-dnd is unmaintained) |
| FastAPI proxy | next.config.ts rewrites + Route Handlers | Rewrites for static serving (zero latency hop); Route Handlers for API calls needing transformation |
| Preview rendering | iframe + postMessage | Python output is the source of truth; re-implementing in React would create a maintenance burden and visual divergence |
| File I/O (local) | New FastAPI endpoints | Simpler than browser File System Access API; consistent with existing Python-centric workflow |
| YAML parsing (client) | `js-yaml` | Mature library, round-trips cleanly with PyYAML-generated YAML, handles all YAML types used in presentation configs |

---

## Sources

- Next.js 16 official docs (version 16.1.6, updated 2026-02-27): proxy/middleware rename, Route Handlers as proxy pattern, rewrites configuration — HIGH confidence ([nextjs.org/docs/app/getting-started/proxy](https://nextjs.org/docs/app/getting-started/proxy), [nextjs.org/docs/app/guides/backend-for-frontend](https://nextjs.org/docs/app/guides/backend-for-frontend))
- Existing codebase: `pf_platform/api.py`, `pf_platform/storage.py`, `templates/present.html.j2` — HIGH confidence (direct read)
- PROJECT.md constraints and milestone definition — HIGH confidence (direct read)
- Zustand ecosystem analysis (2025-2026 community consensus): Zustand preferred over Redux Toolkit for moderate-complexity editor state; Immer middleware for nested mutations — MEDIUM confidence (multiple sources agree)
- `@monaco-editor/react` + `monaco-yaml` packages — MEDIUM confidence (npm, GitHub — actively maintained as of 2025)
- `@dnd-kit/sortable` for drag reorder — MEDIUM confidence (confirmed active maintenance, no deprecation; react-beautiful-dnd confirmed unmaintained)
- `js-yaml` for client-side YAML parse/serialize — HIGH confidence (established library, npm weekly downloads in millions)
- Browser File System Access API limitations — HIGH confidence (MDN, confirmed permission model makes it unsuitable for project-directory workflows)

---

*Architecture research for: Next.js visual editor integration with Python presentation build engine*
*Researched: 2026-03-08*
