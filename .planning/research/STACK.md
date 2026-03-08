# Stack Research

**Domain:** Python presentation engine — rich media, plugin architecture, LLM integration, hosted platform
**Researched:** 2026-03-05 (v0.2 stack) | 2026-03-08 (v0.3 visual editor additions)
**Confidence:** HIGH (v0.2 Python layers, verified PyPI) | MEDIUM (v0.3 JS/Next.js — versions verified via web search March 2026; spot-check npm before scaffolding)

---

## Context: What Already Exists (v0.2.0)

Do not re-add these. This table is the baseline the new stack layers onto:

| Technology | Version (installed) | Role |
|------------|--------------------|----|
| Python | 3.10+ | Runtime |
| Click | 8.x | CLI |
| Jinja2 | 3.x | Template rendering |
| PyYAML | 6.x | Config parsing |
| jsonschema | 4.x | YAML schema validation |
| watchdog | 3.x | Live-reload SSE server |
| Playwright | 1.40+ | PDF export |
| python-pptx | 1.0.2 | PowerPoint export |
| FastMCP / mcp[cli] | 3.1.0 / 1.6+ | MCP server |
| FastAPI | 0.135.1 | REST API (pf_platform) |
| uvicorn | 0.41.0 | ASGI server |
| SQLAlchemy | 2.0.48 | Platform database ORM |
| Plotly.js | CDN | Interactive charts |
| KaTeX | CDN | Math rendering |

---

## Recommended Stack: v0.3 Visual Editor (NEW CAPABILITIES ONLY)

### Core Framework

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Next.js | 16.x (16.1 latest stable) | Visual editor app framework | Next.js 16 is now LTS-stable (released October 2025) with Turbopack as the default bundler (5–10x faster Fast Refresh than webpack), stable React Compiler integration, and explicit opt-in caching that eliminates the aggressive auto-caching footguns in Next.js 13-14. App Router with Server Components is the correct model for this desktop-first tool: shell renders server-side, the slide editor canvas runs client-side. Do NOT use Next.js 15.x — 16 is now stable LTS. |
| React | 19.x | UI components | Peer dependency of Next.js 16. React 19 is stable and required for the React Compiler that Next.js 16 defaults to. No choice here — it comes with Next.js 16. |
| TypeScript | 5.x | Type safety | Next.js 16 ships TypeScript-first. The typed route APIs in Next.js 16 (`Route` generics) require TS 5.x. Not optional — type the FastAPI response shapes and they become the single source of truth for the editor. |

### State Management

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Zustand | 5.x (5.0.11 latest) | Editor global state — slide list, selected slide, dirty state, editor pane sizes | 3KB gzipped. No Provider wrapper needed (critical for Next.js App Router where context providers are cumbersome to thread through server/client boundaries). Works correctly with React 19. The slide editor has straightforward global state: current deck, selected slide index, unsaved changes flag. Zustand handles this with 20 lines. Redux Toolkit is 20x more ceremony for the same result. Jotai is better for derived/interdependent atoms (spreadsheet-like); this editor is not that. |

### Code Editor (YAML/JSON)

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| @uiw/react-codemirror | 4.x (4.25+ latest) | YAML + JSON editing panes in the live editor | CodeMirror 6 over Monaco Editor for this use case. Reasons: (1) Bundle size — Monaco is 2.4MB download; CodeMirror 6 with YAML + JSON extensions is ~300KB. For a desktop-first local tool this matters less, but startup time is still affected. (2) Mobile/embedding — Sourcegraph migrated from Monaco to CodeMirror citing 43% JS download reduction and better mobile behavior. (3) Modular extension system — CodeMirror 6 uses immutable state + facets; YAML and JSON are separate `@codemirror/lang-*` packages pulled in only when needed. `@uiw/react-codemirror` wraps CodeMirror 6 with a clean React API (`value`, `onChange`, `extensions`). |
| @codemirror/lang-yaml | 6.x | YAML syntax support for `presentation.yaml` editing | Official CodeMirror 6 language package. Provides tokenization and indentation rules for YAML. Exact version follows `@uiw/react-codemirror` peer. |
| @codemirror/lang-json | 6.x | JSON syntax support for `metrics.json` editing | Same as above. The editor shows YAML on the left, JSON on the right, with live rebuild on save. |

**Do NOT use Monaco Editor.** 2.4MB download, no modular language imports, and overkill for YAML/JSON editing. Monaco shines for VS Code-style full IDE experiences (100k+ line files, IntelliSense, debugging integration). None of those apply here.

### Drag-and-Drop (Slide Reordering)

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| @dnd-kit/core | 6.x | Drag-and-drop engine | dnd-kit is the current standard for React drag-and-drop (2024–2026). Accessible (ARIA live regions, keyboard support), zero dependencies, ~10KB core. Unlike react-beautiful-dnd (Atlassian, now unmaintained) it handles grids not just lists — important if the slide panel shows a 2-column grid. |
| @dnd-kit/sortable | 10.x | Sortable slide panel preset | Thin preset on top of core. `useSortable` + `SortableContext` gives drag-to-reorder in 30 lines. This is the only use case needed: reorder slides in the left panel. |

**Do NOT use react-beautiful-dnd.** Atlassian deprecated it in favor of `pragmatic-drag-and-drop`. The fork `hello-pangea/dnd` is maintained but limited to lists; the slide panel may need grid layout.

### Resizable Panes (Editor Layout)

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| react-resizable-panels | 2.x | Three-pane editor layout (slide list | YAML/JSON editors | preview) | Lightweight (8KB), pointer-event based (works on desktop + touch), persistence via `onLayout` callback to localStorage. The editor layout is: narrow slide panel left, code editors middle, 1280×720 preview right. `react-resizable-panels` handles this in 15 lines without a third-party hook. Alternative: CSS `resize` handles are too limited (no min/max constraints, no persistence, no keyboard support). |

### UI Components and Styling

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Tailwind CSS | 4.x | Utility CSS for editor UI | Next.js 16 ships with Tailwind v4 integration out of the box. V4 drops the `tailwind.config.js` in favor of CSS-first config (`@theme` in CSS). The presentation framework's existing slide CSS (1280×720px layouts) is isolated from the editor UI — no conflict. |
| shadcn/ui | latest (components copied into project) | Buttons, dialogs, dropdowns, command palette, tabs, sidebar | Not a library — components are copied into `src/components/ui/` and owned by the project. Built on Radix UI primitives (accessible) + Tailwind classes. 65k+ GitHub stars, adopted by Vercel themselves. Provides all the chrome the editor needs: sidebar navigation, toolbar buttons, layout picker dropdown, export dialog. Do NOT reach for another component library (Material UI, Chakra) — they add bundle weight and fight Tailwind. |

---

## Python Backend: No Changes Required

The existing `pf_platform/api.py` FastAPI server already has all the endpoints the visual editor needs:

| Existing Endpoint | Editor Uses It For |
|-------------------|--------------------|
| `POST /build` | Live preview rebuild when YAML/JSON changes |
| `POST /validate` | Validate YAML before sending to build |
| `GET /layouts` | Populate layout picker in editor |
| `WebSocket /ws/{deck_id}` | Optional: present mode sync |

**No new Python packages needed for the editor.** The FastAPI platform already has CORS middleware (`CORSMiddleware` in `pf_platform/api.py`) and all required endpoints.

The one configuration change needed: **ensure `CORSMiddleware` allows `http://localhost:3000`** (Next.js dev server) in the `allow_origins` list.

---

## Frontend-to-Backend Communication

### Development: Next.js Rewrites Proxy (No CORS)

```javascript
// next.config.ts
export default {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:8000/:path*',
      },
    ]
  },
}
```

The browser calls `/api/build` → Next.js dev server forwards to `http://127.0.0.1:8000/build` → FastAPI responds. To the browser, both are `localhost:3000`, so zero CORS issues. This is the standard Next.js + separate backend integration pattern.

**Do NOT set up a separate Express proxy, nginx, or API gateway for local development.** The Next.js rewrites config is 6 lines and eliminates the entire CORS problem.

### Production (Desktop Local Server Mode)

Both servers run locally. The Next.js app is built (`next build` → `next start` on port 3000) and FastAPI runs on port 8000. The same rewrites config handles production too when Next.js is used as the frontend server.

---

## Desktop Deployment: Local Dev Server, NOT Electron or Tauri (Yet)

**Decision: Start with local dev server, evaluate Tauri v2 for a future packaging milestone.**

### Why NOT Electron for v0.3

Electron bundles Chromium (~150MB installer) and Node.js. For a tool that already runs as a local CLI and whose users are developers comfortable with `npm run dev`, this is unnecessary overhead. The existing `pf serve` mental model maps directly to `pf editor` launching the Next.js dev server + FastAPI server together. No Electron needed.

### Why NOT Tauri for v0.3

Tauri v2 + Next.js + Python sidecar is **technically possible** (there are working examples with FastAPI sidecars), but it adds Rust build toolchain, binary bundling for Python, and platform-specific sidecar compilation. This is a significant implementation cost for a milestone focused on building the editor itself. The payoff (smaller bundle, native menus) is real but premature.

### What to Build for v0.3

A `pf editor` CLI command that:
1. Starts the FastAPI platform server in a subprocess (`pf_platform` already exists)
2. Starts the Next.js app (built and served via `next start` or in dev mode)
3. Opens the browser to `http://localhost:3000`

This is 20 lines of Python using `subprocess.Popen` and the existing Click CLI — no new framework required.

**If packaging is needed later (v0.4+):** Tauri v2 is the correct choice over Electron. The `dieharders/example-tauri-v2-python-server-sidecar` repository demonstrates the exact pattern (Tauri + Next.js + FastAPI sidecar). Tauri produces 8–10MB installers vs Electron's 120–150MB. When the project is ready to ship a downloadable app, use Tauri v2.

---

## Installation

```bash
# Scaffold the editor app (run from repo root)
npx create-next-app@latest editor --typescript --tailwind --app --src-dir --import-alias "@/*"
cd editor

# State management
npm install zustand

# Code editor
npm install @uiw/react-codemirror @codemirror/lang-yaml @codemirror/lang-json

# Drag-and-drop
npm install @dnd-kit/core @dnd-kit/sortable @dnd-kit/utilities

# Resizable panes
npm install react-resizable-panels

# shadcn/ui init (copies components into src/components/ui/)
npx shadcn@latest init
# then add individual components as needed:
npx shadcn@latest add button dialog dropdown-menu tabs sidebar command
```

**pyproject.toml: no changes.** The visual editor is a separate `editor/` directory at the repo root — a Next.js app, not a Python package.

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Next.js 16 (App Router) | Vite + React SPA | Use Vite if you never need SSR, file-based routing, or server actions. For a desktop-first local tool, Vite would also work — but Next.js 16 App Router gives server-rendered shells with client islands, which is the right model for this editor (server renders layout chrome, client hydrates the editor canvas). |
| Next.js 16 | Remix | Remix is excellent for web apps with complex nested routing and form-heavy UIs. The presentation editor doesn't have deeply nested routes — it's essentially one editor route with a sidebar. Next.js 16's simpler mental model wins here. |
| @uiw/react-codemirror | @monaco-editor/react | Use Monaco if the project needs VS Code-level features: multi-cursor, global find/replace, diff view, IntelliSense. For YAML and JSON editing in a two-pane layout, this is 2.4MB you don't need. |
| @dnd-kit | react-beautiful-dnd / hello-pangea/dnd | Use hello-pangea/dnd if slide reordering is list-only and you want the simplest possible API. It's a maintained fork with a great DX. But dnd-kit's grid support and accessibility-first design make it the safer long-term choice. |
| react-resizable-panels | allotment | allotment is a solid alternative (VS Code-style panels) with slightly more features. Either works. react-resizable-panels is smaller and has simpler API for a three-pane layout. |
| Local dev server (pf editor) | Electron | Use Electron only if the user base expects a downloadable `.app` / `.exe` with no runtime dependencies. Developer tooling users (the target audience) run CLI tools; `pf editor` launching a browser is expected and sufficient. |
| Tauri v2 (future) | Electron (future) | When packaging becomes a priority, Tauri produces 8–10MB installers vs 120–150MB for Electron. Tauri v2 has confirmed Next.js + FastAPI sidecar support. Use Tauri. |
| Zustand | Jotai | Use Jotai if the editor needs complex derived/interdependent state (e.g., a spreadsheet where changing cell A recomputes B and C). The slide editor's state graph is simple: selected slide index drives preview, dirty flag gates save. Zustand's flat store is cleaner for this. |
| shadcn/ui | Radix UI (raw) | Use raw Radix UI if you don't want Tailwind. If Tailwind is already in the project (it is), shadcn/ui is strictly better — you get the styled components for free, own the source, and can customize without fighting a component library's styling system. |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| @monaco-editor/react | 2.4MB bundle for YAML/JSON editing. VS Code in a browser is overkill when the user is editing 50-line YAML files. Slows initial load noticeably even on localhost. | @uiw/react-codemirror with @codemirror/lang-yaml and @codemirror/lang-json |
| react-beautiful-dnd | Officially deprecated by Atlassian in 2024. The fork hello-pangea/dnd is maintained but limited to list-only drag and has no keyboard ARIA support for grid layouts. | @dnd-kit/core + @dnd-kit/sortable |
| Next.js Pages Router | Next.js 16 App Router is now stable LTS. Pages Router is in maintenance mode. No new project should use it. | Next.js 16 App Router |
| Electron for v0.3 | Adds Rust/Chromium build complexity, 120–150MB binary, and weeks of packaging work to a milestone focused on building the editor. The target users are developers who run CLI tools. | `pf editor` CLI command launching local servers + browser |
| Redux Toolkit | 20x ceremony over Zustand for global state that amounts to: current deck path, selected slide index, dirty flag, pane sizes. Redux is the right call when you have time-travel debugging, complex middleware pipelines, or a large team. | Zustand 5.x |
| next-auth | The visual editor is a local desktop tool — no authentication needed for v0.3. Users run it locally. | No auth — file system access via FastAPI |
| tRPC | tRPC replaces REST with type-safe RPC. Value is highest when both the Next.js app and the backend are in the same TypeScript repo. The backend here is Python/FastAPI. tRPC would duplicate the API layer rather than simplify it. | HTTP fetch to FastAPI REST endpoints, TypeScript types generated from OpenAPI spec |
| SWR or React Query for build calls | Build calls are imperative mutations (user clicks "Build"), not auto-polling data subscriptions. SWR/React Query's cache invalidation and refetch logic adds complexity where `fetch()` + loading state in Zustand is sufficient. | Direct `fetch()` with Zustand loading state |

---

## Stack Patterns by Variant

**If deployment as a standalone app is needed (v0.4+):**
- Add Tauri v2 wrapping the Next.js build
- Bundle FastAPI as a Tauri sidecar (Python binary via PyInstaller)
- Reference: `dieharders/example-tauri-v2-python-server-sidecar` on GitHub
- Rust toolchain requirement: developers must install `rustup`
- Do NOT add Tauri to v0.3 — it doubles the implementation surface

**If the editor needs collaborative multi-user editing (v1.0+):**
- Add Yjs (CRDT library) for conflict-free concurrent editing of the YAML document
- The existing WebSocket sync in `pf_platform/sync.py` handles presenter-push; Yjs handles bidirectional collaborative editing
- Do NOT implement collaborative editing in v0.3 — last-writer-wins via the FastAPI build endpoint is sufficient

**If the editor is deployed as a cloud-hosted web app (not local-only):**
- Move Next.js to Vercel (zero-config deployment, edge functions)
- FastAPI remains on Railway/Render/Fly.io
- Add authentication (Auth.js v5 with GitHub OAuth is the simplest path)
- This is a separate milestone from the local-first v0.3 editor

---

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| Next.js 16.x | React 19.x (required) | Next.js 16 requires React 19. Do not downgrade to React 18. |
| Next.js 16.x | Tailwind CSS 4.x | Next.js 16 ships Tailwind v4 integration; v3 config format (`tailwind.config.js`) is deprecated |
| Zustand 5.x | React 19.x | Zustand 5 supports React 19. Earlier Zustand 4.x also works but misses React 19 concurrent features. |
| @uiw/react-codemirror 4.x | React 18 and 19 | Confirmed React 19 compatible as of v4.25+ |
| @dnd-kit/core 6.x | @dnd-kit/sortable 10.x | Always use the same dnd-kit release family. Core 6 + sortable 10 is the latest matching pair. |
| shadcn/ui components | Tailwind 4.x | shadcn/ui updated all components for Tailwind v4 and React 19 in 2025. Run `npx shadcn@latest` for the current version. |
| FastAPI 0.135.x (existing) | Next.js rewrites proxy | No version dependency — Next.js rewrites forward HTTP/1.1 requests to FastAPI. Any FastAPI version works. |

---

## Sources

- [Next.js 16 release blog](https://nextjs.org/blog/next-16) — stable release October 2025, Turbopack default, React Compiler stable — MEDIUM confidence (web search verified, official source)
- [Next.js 15.5 blog](https://nextjs.org/blog/next-15-5) — Turbopack builds beta, Node.js middleware stable — MEDIUM confidence
- [Next.js Proxy/Rewrites docs](https://nextjs.org/docs/app/getting-started/proxy) — rewrites as CORS-free FastAPI proxy — HIGH confidence (official docs)
- [dnd-kit documentation](https://dndkit.com/) — sortable preset, accessibility — MEDIUM confidence (web search, official site)
- [Top 5 Drag-and-Drop Libraries for React 2026, Puck](https://puckeditor.com/blog/top-5-drag-and-drop-libraries-for-react) — dnd-kit current recommendation — LOW confidence (vendor blog, but aligns with npm data)
- [Sourcegraph: Migrating from Monaco to CodeMirror](https://sourcegraph.com/blog/migrating-monaco-codemirror) — 43% JS reduction, bundle size comparison — HIGH confidence (official engineering blog with measured data)
- [shadcn/ui Tailwind v4 docs](https://ui.shadcn.com/docs/tailwind-v4) — Tailwind v4 compatibility confirmed — HIGH confidence (official docs)
- [Zustand npm](https://www.npmjs.com/package/zustand) — v5.0.11 latest, React 19 compatible — MEDIUM confidence (web search, corroborated by npm)
- [Tauri v2 Next.js guide](https://v2.tauri.app/start/frontend/nextjs/) — Next.js integration pattern — HIGH confidence (official Tauri docs)
- [dieharders/example-tauri-v2-python-server-sidecar](https://github.com/dieharders/example-tauri-v2-python-server-sidecar) — Tauri v2 + Next.js + FastAPI sidecar working example — MEDIUM confidence (community example, not official)
- [Zustand React 19 discussion](https://github.com/pmndrs/zustand/discussions/2686) — React 19 compatibility confirmed — MEDIUM confidence
- `pf_platform/api.py` (codebase) — confirmed `CORSMiddleware` already configured, existing endpoints sufficient — HIGH confidence

---

*Stack research for: presentation-framework v0.3 visual editor (Next.js + React additions)*
*Researched: 2026-03-08*
