# Phase 5: Editor Infrastructure - Context

**Gathered:** 2026-03-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Scaffold a Next.js + React editor app, add a `pf editor` CLI command that starts both Python (FastAPI) and Next.js servers, proxy API calls through Next.js rewrites to FastAPI (no CORS), display an iframe preview of real Python-built slide HTML, and remove rate limits for local editor sessions.

</domain>

<decisions>
## Implementation Decisions

### Editor app shell
- Creative-tool feel (like Figma/Canva) — lighter UI, rounded elements, more whitespace, inviting to non-technical users
- Light mode only — no dark mode in Phase 5
- Layout: top header bar + collapsible left sidebar (placeholder for slide thumbnails in Phase 7) + main canvas area
- Neutral styling — clean grays and whites, no strong brand color in the editor chrome. The slide content is the star, the tool disappears

### Launch experience
- `pf editor [path]` — optional path argument, defaults to current working directory. Consistent with `pf build` pattern
- Minimal terminal output: 2-3 lines ("Starting editor..." then "Editor ready at http://localhost:3000"), clean and quiet
- Auto-opens default browser when ready; `--no-open` flag available for CI/scripting scenarios
- Ctrl+C cleanly kills both FastAPI and Next.js servers — single action, no confirmation prompt

### Preview display
- Iframe scales proportionally (16:9) to fit available canvas space, centered with padding around it. Like Figma's frame preview — always fully visible
- Slide navigation: left/right arrow buttons below the preview + keyboard arrow keys
- Auto-build triggered on project open with a friendly loading state while build runs. Empty state shown if no project found
- Preview toolbar: slide navigation (prev/next/counter) + manual "Rebuild" button. Export and editing controls deferred to later phases

### Project discovery
- No presentation.yaml found → open editor with empty state + "Create new presentation" button (runs `pf init` behind the scenes)
- Phase 5 locks to the project from launch — no switching projects. Phase 6 (Dashboard) adds project browsing
- Metrics detection: convention-based, look for metrics.json in same directory as presentation.yaml. If not found, build without metrics (consistent with CLI behavior)
- Next.js editor source code lives in `editor/` directory at repo root alongside `pf/` and `pf_platform/`

### Claude's Discretion
- Exact color palette for neutral editor chrome (grays, whites, shadows)
- Sidebar width and collapsibility animation/mechanics
- Loading state and spinner design
- Port selection, conflict detection, and fallback behavior
- Rate limit bypass mechanism (header-based, config flag, or separate code path)
- Next.js rewrite URL structure for API proxy
- Editor favicon and window title

</decisions>

<specifics>
## Specific Ideas

- "Like Figma or Canva" — the tool should feel approachable to non-technical users, not like an IDE
- Slide preview should be the hero — centered in the canvas with generous padding, always fully visible at 16:9 ratio
- Terminal output should be minimal and clean, like `npx create-next-app` — not verbose server logs

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `pf_platform/api.py`: FastAPI app with `/api/build` endpoint that accepts config + metrics uploads and returns built deck with warnings. Already has CORS middleware, deck mounting, analytics, and WebSocket sync
- `pf/cli.py`: Click CLI group with existing commands. `platform serve` already starts uvicorn on port 8000 — pattern for the new `editor` command
- `present.html`: Built slide viewer already has keyboard navigation (arrow keys, grid overview, fullscreen) — iframe preview inherits this for free
- `pf/builder.py`: `PresentationBuilder` class handles the full build pipeline — the API endpoint delegates to this

### Established Patterns
- Click CLI with subcommands for new features
- FastAPI + uvicorn for HTTP serving
- `extras_require` in setup.py for optional dependencies (pdf, pptx, platform, etc.)
- Flat-file model: presentation.yaml + metrics.json in a project directory

### Integration Points
- New `pf editor` command in `pf/cli.py` — starts both FastAPI (:8000) and Next.js (:3000) processes
- Next.js rewrites proxy `/api/*` to FastAPI — removes CORS need
- Rate limit on `/api/build` (currently 10/min via slowapi) needs bypass for local editor
- `editor/` directory at repo root for Next.js app source
- New `editor` extra in setup.py for Next.js-related Python dependencies (if any)

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 05-editor-infrastructure*
*Context gathered: 2026-03-08*
