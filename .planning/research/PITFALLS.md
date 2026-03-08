# Pitfalls Research

**Domain:** Presentation engine expansion — rich media, plugin system, LLM integration, hosted platform
**Researched:** 2026-03-05
**Confidence:** HIGH (codebase directly inspected; pitfalls derived from concrete architectural analysis, not generic advice)

---

## Critical Pitfalls

### Pitfall 1: Breaking Backward Compatibility via Schema Tightening

**What goes wrong:**
Adding new layouts (e.g., `map`, `video`, `code`) to the JSON schema `enum` for `layout` is safe. But if you also add stricter `data` shape validation per-layout (the natural next step for LLM structured outputs), any existing `presentation.yaml` that has extra fields the new schema doesn't permit will fail validation. Users who upgrade pip get broken builds on their existing decks.

**Why it happens:**
The current `schema.json` has `"data": {"type": "object"}` — fully open. When adding per-layout schemas (needed for LLM structured output), the impulse is to replace the permissive object with a `oneOf` / `discriminator` that strictly validates each layout's `data`. This is correct for new users but shatters existing decks.

**How to avoid:**
Use `additionalProperties: true` on per-layout data schemas when first introducing them. Strict validation should be opt-in via a `--strict` flag, never the default. Maintain the current open-object default until v1.0 when you can do a formal deprecation.

**Warning signs:**
- Any schema.json PR that removes `"data": {"type": "object"}` in favor of a discriminated union with `required` fields on specific layouts
- Test suite changes that start testing for validation *failure* on old-style config shapes

**Phase to address:** v0.4 (Plugin Architecture) — when per-layout schemas are introduced for LLM use

---

### Pitfall 2: Mermaid.js / Async Library Initialization Race Condition

**What goes wrong:**
Mermaid.js renders diagrams asynchronously after the DOM is ready. In the current iframe-based architecture (`present.html` → `slide_NN.html` iframes), the parent window cannot observe when Mermaid has finished rendering inside the child iframe. During PDF/PPTX export via Playwright's `wait_for_load_state("networkidle")`, Mermaid's async render job runs *after* networkidle fires because it has no network activity — it's pure JS. The resulting screenshot captures the un-rendered placeholder `<pre class="mermaid">` block rather than the diagram SVG.

**Why it happens:**
`networkidle` waits for network requests, not JavaScript execution. Mermaid v10+ uses a Promise-based API (`mermaid.run()` or auto-initialization) that fires on `DOMContentLoaded` but resolves asynchronously. The Playwright `wait_for_load_state` is called in `pptx.py` line 64 and `pdf.py` line 44 — there is no mechanism to wait for JS-driven render completion.

**How to avoid:**
Add a sentinel pattern: after Mermaid renders, set `document.body.dataset.pfReady = 'true'`. In `export_pdf()` and `export_pptx()`, replace `wait_for_load_state("networkidle")` with `page.wait_for_function("document.body.dataset.pfReady === 'true'", timeout=10000)`. Apply the same pattern to any other async library added later (Prism.js auto-highlight, code copy button injection, etc.).

**Warning signs:**
- PDF export tests that use `networkidle` without a JS-ready sentinel
- Mermaid diagrams appear as raw `<pre>` text in exported PDFs
- Tests for export that mock Playwright and skip actual render verification

**Phase to address:** v0.3 (Rich Media) — must be solved before Mermaid is shipped

---

### Pitfall 3: Plugin Layout CSS Leaking Into Core Slides

**What goes wrong:**
A plugin layout ships with its own CSS. If that CSS is injected globally (e.g., written into `theme/` or appended to `base.css`), its styles will affect all slides in the deck — including slides from other layouts. A plugin that changes `--pf-accent` or overrides `.card` will visually break non-plugin slides.

**Why it happens:**
The current build pipeline copies `theme/` as a flat directory. When designing plugin support, the obvious approach is "add plugin CSS to the theme directory." That is wrong. Plugin CSS must be scoped to slides that use that layout.

**How to avoid:**
Each plugin layout template should include its CSS inline via a `{% block head_extra %}` in `base.html.j2` (already present but unused for this purpose). Plugin CSS must use a layout-scoped class prefix (`.pf-layout-mapview`) or CSS custom properties that don't shadow core variables. The builder must inject plugin CSS only into slides that use that layout, never globally.

**Warning signs:**
- Plugin install instructions that say "copy plugin.css to `theme/`"
- Plugin templates that override `--pf-accent`, `--pf-primary`, or any core CSS variable
- The `build()` method accumulating CSS from all installed plugins into a shared stylesheet

**Phase to address:** v0.4 (Plugin Architecture) — CSS isolation must be in the spec before first plugin is built

---

### Pitfall 4: LLM Generates Structurally Valid but Semantically Overloaded YAML

**What goes wrong:**
When an LLM generates a `presentation.yaml`, it reliably produces valid YAML structure (JSON Schema validates correctly) but consistently fills columns to maximum capacity. A `two-column` slide gets 6 cards in the left column. A `data-table` gets 8 table rows. The result is every generated deck fires overflow warnings and displays clipped content. The LLM treats each slide as a document, not a 1280×720px canvas.

**Why it happens:**
The JSON Schema for `data` has no cardinality constraints — `items` in a card's `bullets` array has no `maxItems`. The LLM has no feedback signal from the `LayoutAnalyzer` at generation time. It only sees the schema, which permits unlimited items.

**How to avoid:**
Add `maxItems` constraints to per-layout JSON schemas designed specifically for LLM consumption. These "LLM schemas" are separate from the validation schemas — they are generation guides with tighter bounds (e.g., `"bullets": {"type": "array", "maxItems": 4}`). The `generate_presentation` MCP tool must use these constrained schemas for structured output decoding. The `content_density_optimizer` (v0.5) should then auto-split slides that still overflow after generation.

**Warning signs:**
- `generate_presentation` MCP tool that passes the full `schema.json` directly to the LLM
- Generated decks that consistently have overflow warnings on 60%+ of slides
- No `maxItems` or `maxLength` constraints in any layout schema

**Phase to address:** v0.5 (LLM Integration) — LLM schemas must be distinct from validation schemas from day one

---

### Pitfall 5: Hosted Platform Serving `file://` Slide Assets Breaks in Browser

**What goes wrong:**
The current output is a directory of HTML files with relative paths: `present.html` loads `slide_01.html` in an iframe via a relative path; slides load `theme/variables.css` via a relative path. This works perfectly for `file://` and local `http://`. When moving to a hosted platform where slides are stored in object storage (S3/R2) and served via CDN, all relative paths break. An uploaded `present.html` cannot load `theme/variables.css` via a relative path if CSS is served from a different path prefix or bucket structure.

**Why it happens:**
The entire build pipeline was designed for local filesystem use. The `present.html.j2` template hardcodes relative path references: `src="{{ slides[0] }}"`, `href="theme/variables.css"`. There is no concept of a base URL or asset manifest.

**How to avoid:**
Before building the platform layer, introduce an `--base-url` build option that rewrites asset paths at build time. Better: generate a `manifest.json` listing all assets, and have the platform uploader resolve absolute URLs from the manifest. This is a single build pipeline change that unblocks everything in v1.0.

**Warning signs:**
- Platform prototype where CSS/JS assets are served as broken 404s when opened from CDN URL
- Attempts to "fix" this with CORS headers rather than fixing the path model
- `present.html` template still using bare relative paths when the platform phase starts

**Phase to address:** End of v0.3 or start of v1.0 — path abstraction must be added before platform upload is implemented

---

### Pitfall 6: Playwright Spawning One Browser Process Per Slide

**What goes wrong:**
The current `export_pdf()` and `export_pptx()` correctly reuse a single browser context across all slides (one `sync_playwright()` context, one `new_page()` per slide). The `pptx_native.py` `_render_image_fallback()` does NOT — it calls `sync_playwright()`, `chromium.launch()`, and `browser.close()` inside a loop per slide. For a 20-slide deck where 17 slides need image fallback, this spawns and kills 17 Chromium processes. Build time goes from ~15 seconds to ~3 minutes, and the process can fail on systems with low file descriptor limits.

**Why it happens:**
`_render_image_fallback()` is called per slide and was written as a standalone function. Each call is self-contained. It's not obvious it's inside a loop until you trace `export_pptx_editable()`.

**How to avoid:**
Refactor `_render_image_fallback()` to accept an existing Playwright `page` object as a parameter. The `export_pptx_editable()` orchestrator creates a single browser context at the top and passes pages to fallback renderers. This is the same pattern already used correctly in `pptx.py`.

**Warning signs:**
- Export of a 20-slide mixed (native + fallback) deck takes more than 60 seconds
- System logs showing 15+ Chromium processes spawned and killed during one export
- `_render_image_fallback` that calls `sync_playwright()` as its first line

**Phase to address:** v0.3 (finish editable PPTX) — fix before expanding native renderer coverage

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Hardcoding CDN library versions (`plotly-2.35.2.min.js`, `katex@0.16.11`) in templates | Simple, reproducible | CDN URLs go stale; security vulnerabilities not patched | Only until v0.4; should move to configurable version or integrity-hashed URLs |
| `autoescape=False` in Jinja2 Environment | Allows raw HTML in slide content | XSS risk if user input (from LLM or API) reaches templates without sanitization | Acceptable for CLI (user owns the input); NOT acceptable once a hosted REST API or `generate_presentation` tool processes untrusted LLM output |
| `LayoutAnalyzer` height estimates as hardcoded magic numbers (`SIZE_MODEL` dict) | Simple to implement | Estimates become wrong when CSS changes (new block types, font size changes); no feedback loop | Only at current scale; should be replaced by a headless render check in v0.5 |
| Single flat `metrics.json` | Simple data model for users | Complex presentations need namespaced data; name collisions become frequent; no data source typing | Acceptable for v0.3; data source plugins in v0.4 need a typed source registry model |
| Plugin CSS injected via `{% block head_extra %}` | Easy to implement | No isolation enforcement — plugins must self-police; a careless plugin can still break everything | Never for CSS variables; only for scoped class selectors |

---

## Integration Gotchas

Common mistakes when connecting to external services.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Google Maps Embed API | Using the dynamic Maps JavaScript API with an API key visible in HTML source | Use the Maps Static API for export-safe static images; use the Embed API (no JS key exposure) for interactive HTML. The API key must be a build-time secret, never in the output HTML |
| YouTube/Vimeo embed | Using `<iframe src="https://www.youtube.com/embed/ID">` directly in a slide — this loads fine in browser but Playwright `networkidle` never fires because YouTube's JS keeps requesting analytics data | Use `<iframe src="https://www.youtube-nocookie.com/embed/ID?autoplay=0">` and set a hard timeout for export screenshots |
| Mermaid.js | Calling `mermaid.initialize({startOnLoad: true})` and then doing nothing — diagram renders in browser but not in Playwright export (see Critical Pitfall 2) | Use the explicit `mermaid.run()` promise with a `data-pf-ready` sentinel |
| External fonts (Google Fonts) | Slides look correct in browser but fonts render as fallback in PDF/PPTX exports because Playwright's sandboxed Chromium doesn't always have network access | Pre-download font files and serve from `theme/fonts/` directory; add a `--offline-fonts` build flag |
| Python `importlib.metadata.entry_points` | Using the Python 3.8 API (`entry_points()["group"]` dict-style) — this is deprecated and removed in Python 3.12; breaks silently on some versions by returning empty | Use `entry_points(group="pf.layouts")` keyword form (Python 3.12+ compatible) |

---

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Grid overview loads all iframes simultaneously | Opening grid overlay (G key) with 30+ slides causes browser to render 30 iframes at once; tab freezes for 3-5 seconds | `loading="lazy"` is already set on thumb iframes — verify it works cross-browser; add Intersection Observer for progressive reveal | At ~20 slides in the grid overlay |
| Building slides sequentially in a single Python process | 50-slide deck build takes 8+ seconds because each Jinja2 render is synchronous and templates are not cached between slides | Jinja2's `Environment` already caches compiled templates — this is handled correctly. Watch for any future change that creates a new `Environment` per slide | Not currently a trap — only becomes one if `Environment` is re-instantiated |
| `_render_image_fallback()` per-slide browser spawn | Export of 20+ mixed slides takes minutes (see Critical Pitfall 6) | Single browser context, pass `page` objects to renderers | >5 fallback slides in one export |
| Playwright `wait_for_load_state("networkidle")` with long timeout | REST API or platform build endpoint hangs for 30 seconds per slide when a CDN resource is slow | Set explicit shorter timeouts; use `wait_for_function` on a ready sentinel instead | Any time a CDN is slow or throttled |
| Streaming SSE reload from `pf serve` blocks a thread per connected client | Multiple browser tabs watching the same deck hold open persistent SSE connections; each blocks a Python thread in `SimpleHTTPRequestHandler` | Not an issue for single-developer local use. Must be replaced with async server (FastAPI/Starlette) before hosting multiple users | >3 concurrent SSE clients |

---

## Security Mistakes

Domain-specific security issues beyond general web security.

| Mistake | Risk | Prevention |
|---------|------|------------|
| `autoescape=False` on Jinja2 Environment + LLM-generated content | An LLM generating slide content could produce `<script>` tags or `javascript:` URIs that execute in the viewer's browser when the hosted platform serves slides | Enable `autoescape=True` for any path where template variables come from LLM output or user-submitted data; use `| safe` filter only on values from trusted internal sources (the builder's own HTML blocks) |
| Google Maps API key in HTML output | Key exposed to anyone who views source; can be abused for quota theft | API keys must be server-side secrets; for hosted platform, the Maps API call must be proxied through the backend, not embedded in client HTML |
| Plugin directory traversal via `layouts/` directory discovery | Plugin system that scans a user-configured `layouts/` directory could be abused (e.g., `layouts/../../../../etc/passwd.html.j2`) if the directory is user-controllable via a hosted API | Validate that all discovered layout template paths resolve to within the configured plugin directory; use `Path.resolve()` with a parent-check before loading |
| `yaml.safe_load()` is correct — never `yaml.load()` | YAML deserialization with `yaml.load()` executes arbitrary Python | This is already done correctly (`yaml.safe_load()` in `builder.py`). Flag any future code that uses bare `yaml.load()` — it will appear in auto-generated code suggestions |
| Hosted REST API with no rate limiting on `build_presentation` | An LLM agent in a runaway loop could trigger thousands of build requests; each spawns a Chromium process | Any hosted API endpoint wrapping `build_presentation` needs per-token/per-IP rate limiting before v1.0 |

---

## UX Pitfalls

Common user experience mistakes in this domain.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Mermaid/code block requiring separate `theme.diagrams: true` flag (like `theme.charts`) | Users add code blocks without the flag; build succeeds silently but the library is absent at runtime; block renders as unstyled text | Either auto-detect required libraries from slide content during build and auto-include them, or emit a clear build warning when a layout block type requires a library flag that isn't set |
| Plugin install instructions that require editing `presentation.yaml`'s `theme:` section | Non-technical users who run the CLI as a tool don't know how to "activate" a plugin | Plugins should be auto-discovered by Python entry points or by existence in `~/.pf/plugins/`; no manual YAML editing required |
| `generate_presentation` MCP tool that returns YAML as a string | LLM agents receive the YAML string and must write it to disk themselves, creating an extra tool call and potential path confusion | The tool should accept an optional `output_path` and write the files directly, returning the path as the result |
| Video embeds that autoplay during presentation | Presenter advances to a slide; video starts playing with sound during the talk | All video embeds must default to `autoplay=false`; autoplay only if explicitly set in YAML |
| Overflow warnings that don't identify which specific block is too tall | User gets "col left ~620px of 575px usable (7% over)" but doesn't know which of 4 cards is the problem | Enhance `LayoutAnalyzer` to include the block type and index in the warning: "two-column left col: card[2] is estimated 180px — try reducing bullets from 6 to 3" |

---

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **Mermaid.js diagrams:** Render correctly in browser — verify they also render in PDF/PPTX export with the `data-pf-ready` sentinel pattern before shipping
- [ ] **Plugin layouts:** Load and render in browser — verify they are also included in the MCP `list_layouts()` and `get_layout_example()` tools, otherwise agents can't use them
- [ ] **Editable PPTX native renderers:** Section/quote/closing look correct — verify `title` layout (with icon grid) also has a renderer, or document explicitly that it falls back to image
- [ ] **`generate_presentation` MCP tool:** Returns valid YAML — verify the YAML also passes `validate_config()` and the resulting deck has zero overflow warnings on a test corpus of 10 prompts
- [ ] **Hosted web viewer:** Slides display correctly from CDN URL — verify `theme/variables.css` and `theme/base.css` are resolved correctly at the CDN path, not just from the build output directory
- [ ] **Code syntax highlighting:** Colors look correct in browser — verify background color respects the slide's `--pf-primary` theme color, not a hardcoded dark/light assumption
- [ ] **Fragment/progressive builds:** Clicking through builds works in present.html — verify fragment state is reset correctly when navigating *backward* to a slide (common failure: backward navigation shows all fragments already revealed)
- [ ] **Data source plugins (Google Sheets etc.):** Data resolves at build time — verify build still produces a warning if the source is unreachable, rather than silently producing slides with empty data

---

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Schema tightening breaks existing user YAMLs | HIGH | Ship a migration script (`pf migrate --from 0.3 --to 0.4`) that updates YAML to new schema; provide a `--schema-version 0.3` legacy mode; announce deprecation 2 releases in advance |
| Mermaid export renders as `<pre>` text in published PDFs | MEDIUM | Add the `data-pf-ready` sentinel to the Mermaid template; rebuild all affected presentations; no data loss, just a rebuild |
| Plugin CSS leaks into core slides | MEDIUM | Identify the offending plugin's CSS by bisecting; add a CSS prefix requirement to plugin spec; plugin authors must update their packages |
| LLM generates all slides at maximum density | LOW | The `content_density_optimizer` (v0.5) can auto-split the deck post-generation; short-term: add `maxItems` constraints to LLM schemas |
| Hosted platform breaks on relative asset paths | HIGH | Requires a build pipeline change to output absolute URLs; all previously uploaded decks must be rebuilt and re-uploaded; plan this before the first public upload feature ships |
| Playwright spawning per-slide browsers (build timeout) | LOW | Refactor `_render_image_fallback()` to accept an existing `page` object; no user-facing changes required |

---

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Backward compatibility (schema tightening) | v0.4 start — before per-layout schemas are added | Existing v0.2 demo presentation builds without error on new validator |
| Mermaid async export race condition | v0.3 — before Mermaid feature ships | PDF export test captures rendered SVG, not `<pre>` placeholder |
| Plugin CSS isolation | v0.4 start — before first layout plugin is written | Two conflicting plugins installed simultaneously do not affect each other's slides |
| LLM generates overloaded slides | v0.5 start — before `generate_presentation` tool ships | Generated deck from 10 diverse prompts has <20% overflow rate |
| Hosted platform relative path breakage | v0.3 end / v1.0 start — before upload feature | Deck uploaded to S3 and served from CDN URL loads all assets correctly |
| Per-slide Playwright browser spawn | v0.3 — before expanding native PPTX renderers | 20-slide mixed deck exports in <45 seconds |
| `autoescape=False` + LLM input | v0.5 — before `generate_presentation` processes untrusted input | XSS payload in LLM-generated title field does not execute in viewer |
| API rate limiting | v1.0 — before hosted REST API is public | Load test: 100 concurrent build requests are rate-limited, not processed |

---

## Sources

- Codebase direct analysis: `pf/builder.py`, `pf/pptx_native.py`, `pf/pdf.py`, `pf/mcp_server.py`, `pf/analyzer.py`, `pf/schema.json`, `templates/base.html.j2`, `templates/present.html.j2`
- Architecture documents: `docs/plans/2026-03-05-roadmap-design.md`, `docs/plans/2026-03-05-editable-pptx-poc.md`
- Domain knowledge: Jinja2 autoescape behavior, Playwright `wait_for_load_state` semantics, Python `importlib.metadata` version compatibility, Mermaid.js v10 async initialization model, YAML safe_load vs load security, Python entry point discovery patterns

---
*Pitfalls research for: Presentation Framework v0.3–v1.0 expansion*
*Researched: 2026-03-05*

---
---

# Visual Editor Pitfalls (v0.3 Milestone)

**Domain:** Adding a Next.js + React visual editor to an existing Python build-pipeline tool
**Researched:** 2026-03-08
**Confidence:** MEDIUM-HIGH (primary: architectural analysis of existing codebase; secondary: community patterns from React editor projects, Electron/Tauri docs, Node-Python IPC docs)

---

## Critical Pitfalls

### Pitfall 7: Preview Fidelity Divergence — Editor Shows What Never Builds

**What goes wrong:**
The editor renders a React approximation of each slide layout while the actual build output is Jinja2 HTML served from Python. These two rendering paths diverge immediately and permanently. Typography (font loading order, CSS cascade), layout math (CSS Grid exact column fractions), responsive behavior of the 1280x720 viewport, and JavaScript-driven features (Plotly charts, KaTeX math, Mermaid diagrams, Highlight.js) all differ between the React preview and the real output. Users make edits that look correct in the editor and then build to find misaligned columns, wrong font weights, or blank chart placeholders.

**Why it happens:**
Developers build a quick React component per layout for speed ("we'll sync them later"), but the CSS in `theme/variables.css`, `theme/base.css`, and `theme/layouts.css` is the source of truth — not the React components. The Python Jinja2 templates use CSS custom properties derived from hex colors at build time; the React components use inline styles or Tailwind that approximate but never match. Two rendering engines means two codebases to keep synchronized, and they drift.

**How to avoid:**
Use the actual built HTML output as the preview. Serve the Python-built `slide_NN.html` inside a scaled `<iframe>` within the editor. The iframe displays the real Jinja2 output — zero divergence by construction. The editor's job is to edit the YAML/data model and trigger rebuilds; it is NOT responsible for rendering slides. This is the approach used by tools like Directus visual editor (iframe preview against the actual renderer).

Concrete implementation: iframe with `srcdoc` set to the built slide HTML, scaled via `transform: scale(factor)` + `transform-origin: top left` to fit the editor panel. The scale factor is `panelWidth / 1280`.

**Warning signs:**
- A `SlidePreview.tsx` component that renders layout-specific JSX (`if layout === 'two-column': <TwoColumnPreview ...>`)
- Editor CSS that imports from `theme/` copied into `public/` — any copy means they will diverge on next theme change
- Preview panel that works without the Python process running

**Phase to address:** Phase 1 (Editor foundation) — the iframe-based preview architecture must be decided on day one; retrofitting after building React layout components is a partial rewrite

---

### Pitfall 8: State Management Explosion — Two Sources of Truth for the Same Slide

**What goes wrong:**
The editor maintains a React state tree (`slides[]`, `theme`, `metrics`) that the user edits via forms. There is also the canonical `presentation.yaml` file on disk. When users switch between the visual form editor and the raw YAML code editor, the two representations must stay in sync. They don't. A user edits YAML directly (adding a comment, changing indentation), switches to the form view, the form re-parses YAML and loses their comments, they switch back and the YAML looks different. Round-trip parsing breaks user expectations and erodes trust.

Beyond that: undo/redo must span both editors. A user who types in the YAML editor, then clicks a form field, then hits Cmd+Z expects the YAML change to undo — not the form change. Implementing undo history across two synchronized state representations requires a central command log, not two separate `useReducer` stacks.

**Why it happens:**
The natural React approach is to put form state in `useState`/`useReducer`, separately parse the YAML into a different state shape for the code editor (Monaco's internal model), and try to sync them with `useEffect`. This creates the classic two-source problem: any edit to one representation must be propagated to the other, with all the edge cases of partial edits, parse failures (mid-type invalid YAML), and async sync races.

**How to avoid:**
YAML file on disk is the single source of truth. The editor's in-memory state is a parsed AST of the YAML. The form editor writes to the AST. The code editor displays and edits the AST serialized as YAML. Undo/redo operates on AST snapshots. Use a single Zustand store with:
- `yamlText: string` (the raw text, shown in code editor)
- `parsedState: PresentationConfig` (the typed object, fed to forms)
- `history: PresentationConfig[]` (undo stack)

On any edit: update `parsedState` → serialize to `yamlText` → push to `history`. The code editor uses `yamlText` as display; forms use `parsedState`. YAML comments are lost on the first round-trip (this is acceptable and must be documented, not fixed).

Use `ruamel.yaml` (Python) on save to preserve ordering if comments matter for the user's workflow.

**Warning signs:**
- Two separate `useState` hooks for `yamlContent` and `slideData` in the same component
- `useEffect` that syncs `yamlContent` changes to `slideData` (sync-via-effect is the anti-pattern)
- Undo that only works in the code editor panel, not in the form panel

**Phase to address:** Phase 1 (Editor foundation) — state architecture must be locked before any feature panel is built; retrofitting Zustand later when forms are already written means rewriting all form components

---

### Pitfall 9: Rebuild Latency Kills the Live Preview Experience

**What goes wrong:**
A user types a character in the title field. The editor triggers a rebuild of the full presentation. The Python builder runs Jinja2 for all 12 slides, writes HTML files to disk, and the preview iframe refreshes. This takes 800ms–2s. Typing feels laggy. The user stops interacting with the editor and goes back to editing YAML in their text editor directly — defeating the purpose of the editor.

**Why it happens:**
The natural implementation calls the existing `/api/build` endpoint on every state change (debounced). The builder builds all slides even when only slide 3's title changed. The iframe reload flashes white during refresh. Each rebuild is also a full disk write for all slides.

**How to avoid:**
Three techniques in combination:

1. **Debounce aggressively**: 600–800ms debounce after last keypress before triggering rebuild. VS Code Live Preview uses 50ms for file changes; for typed content, 600ms feels responsive but avoids "build storm" from fast typists.

2. **Single-slide rebuild**: Add a `--slide-index N` option to the Python builder (or a `/api/build/slide/N` endpoint) that rebuilds only the slide currently visible in the preview. For the editor's preview panel, only the active slide needs to be current. Full rebuild runs on save/export.

3. **Iframe `srcdoc` refresh without flashing**: Instead of setting `iframe.src` to a new URL (causes white flash), use `iframe.srcdoc = newHtml` to update content in-place, or use `postMessage` to the iframe to hot-patch the slide content without a full reload.

**Warning signs:**
- Preview update that sets `iframe.src = '/slides/slide_03.html?' + Date.now()` (causes white flash on every keystroke)
- Build trigger on `onChange` handler without debounce
- Full deck rebuild on single-field change

**Phase to address:** Phase 2 (Live YAML/JSON editor with preview) — the single-slide rebuild endpoint should be added to the Python backend before the editor's preview panel is wired up

---

### Pitfall 10: Node.js-to-Python Cross-Process Communication Failures

**What goes wrong:**
The Next.js editor calls the existing FastAPI platform to trigger builds. In local desktop deployment (no Tauri/Electron — just two processes), the Node.js server needs to either call FastAPI over HTTP or spawn the Python `pf` CLI as a child process. The HTTP approach works but requires the user to manually start both processes. The child process approach has silent failures: stdout buffering in Python means responses don't reach Node until the process exits; stderr goes to `/dev/null`; the Python process crashes silently on import errors; and there is no way to know if the Python backend is running at all.

**Why it happens:**
Node's `child_process.spawn()` with stdin/stdout IPC seems simple but Python's stdout is block-buffered by default (not line-buffered). Without `sys.stdout.flush()` or running Python with `-u` flag, responses are buffered in the OS pipe and never arrive. Developers test with short scripts where the process exits (flushing the buffer on exit) and conclude it works, then ship it and find it fails for long-running processes.

**How to avoid:**
Use HTTP over localhost exclusively — do not use stdin/stdout IPC between Node.js and Python. The architecture should be:
- User runs `pf serve` (FastAPI on port 7749) — one process
- User runs `npm run dev` (Next.js on port 3000) — second process
- Next.js calls FastAPI on `http://localhost:7749` for all build operations
- Provide a `pf editor` CLI command that starts both processes (using Python `subprocess.Popen` to start Next.js, or a shell script)

If spawning Python as a child of Node.js is required, run Python with `python3 -u` (unbuffered) and add `sys.stdout.flush()` after every response write. Use newline-delimited JSON (NDJSON) as the message protocol.

**Warning signs:**
- Node.js code that calls `child_process.spawn('python3', ['pf/builder.py'])` and reads from stdout
- Missing `sys.stdout.flush()` in any Python script meant to be called as a Node child process
- Editor that requires both processes to be started separately with no orchestration
- Health-check endpoint missing from FastAPI (no way to verify Python is running before making build calls)

**Phase to address:** Phase 1 (Editor setup/architecture) — the process model must be decided before any API calls are implemented; retrofitting process management after building the UI is painful

---

### Pitfall 11: YAML Editing UX — Destroying User-Authored Comments and Formatting

**What goes wrong:**
Users craft `presentation.yaml` files with inline comments explaining slide content (`# Key metric — update before Q3 board meeting`), deliberate blank lines separating slides for readability, and their own indentation style. When the visual editor reads the YAML, modifies a field via the form, and writes YAML back to disk, all comments are stripped and formatting is normalized by PyYAML's `yaml.dump()`. The file the user returns to in their text editor is unrecognizable. They stop using the visual editor for anything they care about.

**Why it happens:**
PyYAML's `yaml.dump()` does not preserve comments or blank lines — it serializes from the parsed Python dict. This is not a bug; it's by design. Almost every editor that reads-modifies-writes YAML has this problem unless specifically engineered around it.

**How to avoid:**
Three-layer strategy:
1. **Write-only on explicit save**: Never auto-save YAML back to disk during editing. The in-editor state is the YAML. The file on disk is only written when the user explicitly clicks Save (Cmd+S). This gives users control over when their file is touched.
2. **Preserve via code editor as canonical**: The Monaco code editor panel is the YAML source. Form changes serialize to the Monaco buffer (in-memory), not to disk. The user decides when to write the buffer to disk.
3. **Use `ruamel.yaml` for round-trip fidelity**: `ruamel.yaml` (Python) is specifically designed for round-trip YAML parsing that preserves comments, ordering, and formatting. If the editor must write YAML programmatically, use `ruamel.yaml` instead of PyYAML.

Document clearly: if the user edits exclusively through forms (never touching the YAML editor), comments will not be preserved on first save. This tradeoff is acceptable and expected.

**Warning signs:**
- Save function that calls `yaml.dump(parsed_state)` directly
- Auto-save on every form change that writes to the file on disk
- No Monaco code editor panel (form-only UX removes user's escape hatch)

**Phase to address:** Phase 2 (Live YAML/JSON editor) — YAML fidelity policy must be documented and encoded in the save flow from day one

---

### Pitfall 12: Drag-and-Drop Slide Reordering Complexity and Accessibility Gaps

**What goes wrong:**
Slide reordering is added as "a simple drag-and-drop feature" using a library like `react-dnd`. It works on mouse/trackpad. Then: keyboard users cannot reorder slides at all; touch screen (iPad) users get broken drag behavior; the drag preview shows a tiny unreadable thumbnail; dropping a slide in the wrong spot with no undo is destructive; and the YAML array reorder must be instantly reflected in the editor state without triggering a rebuild.

**Why it happens:**
Drag-and-drop looks simple for pointer devices but has hidden complexity: (1) accessibility requires keyboard equivalents (up/down arrow, Enter to confirm); (2) mobile/touch requires pointer event handling distinct from mouse events; (3) the sortable list must work with React's virtual DOM without causing full re-renders of all slide thumbnails; (4) undo must cover the reorder operation.

**How to avoid:**
Use `@dnd-kit/sortable` (not `react-beautiful-dnd` — deprecated and unmaintained by Atlassian). `dnd-kit` has first-class keyboard support, touch support, and accessibility announcements built in. It uses CSS transforms (not DOM reordering) during drag, which prevents layout thrash. Wire the `onDragEnd` callback to a single Zustand action that: (1) reorders the `slides[]` array in state, (2) pushes to the undo stack, and (3) serializes to YAML in-memory without triggering a rebuild.

Do not implement drag-and-drop before undo/redo is working. A destructive operation without undo is a support ticket.

**Warning signs:**
- Drag-and-drop implemented before the undo/redo history stack is built
- Using `react-beautiful-dnd` (deprecated; Atlassian stopped maintaining it in 2023)
- No keyboard shortcut (Ctrl+Up/Ctrl+Down) as a fallback for slide reordering

**Phase to address:** Phase 3 (Visual slide editor) — implement only after undo stack is in place in Phase 2

---

### Pitfall 13: Desktop Deployment Without a Wrapper — Two-Process User Experience

**What goes wrong:**
The editor requires two processes: `pf serve` (Python/FastAPI on port 7749) and `npm run dev` / `next start` (Node.js on port 3000). Users must start both manually, keep both terminal windows open, and handle port conflicts. When one process crashes, the other continues running silently. Users think the editor is broken when actually only one backend crashed. Developers who "just want to edit their slides" instead troubleshoot process management.

**Why it happens:**
Developers run both processes in separate terminals during development and forget this is a terrible user experience. Shipping a `package.json` script with `concurrently` helps developers but is not a user-deployable solution.

**How to avoid:**
Provide a `pf editor` CLI command (Python Click) that:
1. Starts the FastAPI server as a subprocess (`subprocess.Popen`)
2. Starts the Next.js dev server (or static export served by FastAPI)
3. Opens the browser to `http://localhost:3000`
4. Handles Ctrl+C to kill both subprocesses cleanly
5. Prints clear status when either subprocess crashes

For packaging, prefer serving the Next.js app as a static export (`next export`) from the FastAPI backend — one process, one port, no Node.js runtime required in production. This means FastAPI serves `/_next/static/` as static files and handles all API routes.

Do NOT use Electron or Tauri for v0.3. Electron adds 150MB+ to the binary, has complex Next.js integration issues (Next.js SSR and API routes don't work cleanly in Electron's renderer process), and requires a separate build pipeline. Tauri uses Rust for the main process (added learning curve) and requires PyInstaller to bundle the Python backend as a sidecar binary — a non-trivial build step. Both are addressable in a later dedicated packaging milestone if desktop distribution becomes a priority.

**Warning signs:**
- Documentation that says "start the Python backend in one terminal and the Next.js server in another"
- No `pf editor` command in `pf/cli.py`
- Next.js configured with `output: 'standalone'` (for containers) instead of `output: 'export'` (for static files served by FastAPI)

**Phase to address:** Phase 1 (Editor setup) — the deployment model determines the Next.js build configuration from the start

---

## Technical Debt Patterns (Visual Editor)

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| React layout preview components (not iframe) | Faster to build, no Python dependency for preview | Permanent divergence from actual build output; maintenance burden to keep React and Jinja2 in sync | Never — the iframe approach has the same dev speed after Phase 1 |
| Auto-save YAML on every form change | Feels like Google Docs | Destroys comments, formatting; creates noisy git diffs; makes file-based collaboration painful | Never for file writes; acceptable for in-memory state only |
| Single "rebuild all" button rather than live preview | Simple to implement | Users lose the "see it as you type" experience; editor feels like a fancy form wrapper | Only for export flows; live preview should still use single-slide rebuild |
| Embedding Next.js in Electron immediately | Native desktop feel | 150MB+ app size; complex build pipeline; Next.js SSR incompatible with Electron renderer | Never for v0.3; evaluate after static export model is proven |
| Using `react-beautiful-dnd` | Well-documented, familiar | Deprecated and unmaintained since 2023; keyboard accessibility is poor | Never; use `@dnd-kit/sortable` |
| Monaco editor bundled in full | Best YAML editing experience | Adds ~2MB to the JS bundle; may cause issues with Next.js code splitting if not lazy-loaded | Acceptable if lazy-loaded via `next/dynamic` |

---

## Integration Gotchas (Visual Editor)

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| FastAPI CORS for Next.js dev server | Forgetting CORS headers on FastAPI when Next.js dev runs on a different port | Add `fastapi.middleware.cors.CORSMiddleware` with `allow_origins=["http://localhost:3000"]` to the platform FastAPI app; remove the wildcard `*` before production |
| iframe `srcdoc` and JavaScript libraries | Setting `iframe.srcdoc` with slide HTML that loads Plotly/KaTeX/Mermaid from CDN — these CDN requests may be blocked by the browser's CSP if the parent page has a restrictive CSP | Set the parent Next.js page CSP to permit CDN sources used by slides, or use `sandbox="allow-scripts allow-same-origin"` on the preview iframe |
| Next.js static export and dynamic routes | Using Next.js dynamic routes (`/slides/[id]`) that require a Node.js server — these don't work with `next export` (static export) | Use hash-based routing or query params for navigation in the static export; all routes must be pre-rendered at build time |
| Monaco editor and Next.js SSR | Importing Monaco at the top level causes SSR failures because Monaco uses browser-only APIs | Always import Monaco via `next/dynamic` with `{ ssr: false }` |
| YAML parse errors during editing | Parsing YAML on every keystroke causes parse errors on partial input (user is mid-word) — this floods error state with false positives | Parse only on debounce (600ms after last keypress); show "invalid YAML" indicator without clearing the form state |

---

## Performance Traps (Visual Editor)

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Re-rendering all slide thumbnails on every state change | Slide panel flickers on every keystroke; CPU spikes visible | Memoize thumbnail components with `React.memo`; thumbnail only re-renders when its specific slide data changes | >8 slides in the thumbnail panel |
| Full deck rebuild on single-field change | Preview update takes 1-2 seconds; typing feels laggy | Single-slide rebuild endpoint in Python; debounce 600ms; update only the currently-previewed slide | Any deck with more than 3 slides |
| iframe reload flash on preview update | White flash every time preview updates; disorienting | Use `srcdoc` update instead of `src` URL change; or use `postMessage` to hot-patch slide content | Every preview refresh |
| Undo history unbounded growth | After 200 edits, memory grows visibly; Cmd+Z starts lagging | Cap undo history at 50 states; use structural sharing (Immer) to avoid full state copies | >50 undoable actions in a session |
| Monaco editor always loaded even on template gallery page | 2MB JS loads even when user is just browsing templates | Lazy-load Monaco via `next/dynamic({ ssr: false })` only when the YAML editor panel is first shown | Any page that doesn't need the code editor |

---

## Security Mistakes (Visual Editor)

| Mistake | Risk | Prevention |
|---------|------|------------|
| iframe preview with `allow-scripts allow-same-origin` sandbox combination | A malicious YAML file that generates slide HTML with `<script>` can break out of the sandbox and access the parent page's origin — this combination effectively disables sandbox protection | Use `allow-scripts` only (without `allow-same-origin`); the slide HTML won't be able to access localStorage or cookies of the editor origin |
| YAML file path traversal via editor save | An editor that accepts a user-provided save path could write files to arbitrary locations if the path is not validated | The FastAPI save endpoint must validate that the target path resolves within the user's projects directory; use `Path.resolve()` and a parent-check |
| Serving built slide HTML with no CSP | The built slides may contain user-supplied content (LLM-generated titles, bullets); without CSP, XSS in slide HTML can affect the parent editor page | Slide preview iframes must have restrictive CSP; alternatively, serve built slides on a different origin from the editor (e.g., `localhost:7749/preview/` vs the editor on `localhost:3000`) |

---

## UX Pitfalls (Visual Editor)

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| No visual indication that a rebuild is in progress | User edits title, preview doesn't update for 800ms, user thinks the editor is broken and clicks multiple times | Show a subtle spinner or "rebuilding..." indicator in the preview panel during the debounce window and rebuild |
| Layout picker shows names only (`two-column`, `data-table`) | Non-technical users don't know what these mean | Show a thumbnail screenshot of each layout; generate these once from the built example slides |
| Form editor that hides the YAML editor | Power users who discover the YAML edit view and switch to it feel like they're bypassing the editor, not using it | The YAML editor is a first-class panel, not a debug escape hatch; make it equally prominent to the form editor |
| Slide thumbnail click navigates to slide without confirming unsaved changes | User clicks a different slide; unsaved changes to current slide are lost with no warning | Track "dirty" state per slide; warn before navigating away if there are unsaved changes |
| Export button that runs the full Python build and opens a file picker in-browser | File picker for saving to disk requires File System Access API (not available in all browsers/contexts) | Use a server-side download endpoint (`/api/export/pdf?deck=path`) that streams the file, triggering browser download natively |

---

## "Looks Done But Isn't" Checklist (Visual Editor)

- [ ] **Live preview:** Updates when user types — verify update also works when switching between slides in the thumbnail panel (not just on keystroke)
- [ ] **YAML round-trip:** Form edits serialize back to valid YAML — verify the serialized YAML builds successfully via `pf build` without manual edits
- [ ] **Undo/redo:** Works in form panel — verify it also works when switching between form and code editor panels (cross-panel undo)
- [ ] **Slide reorder:** Drag-and-drop works with pointer — verify it also works with keyboard (Ctrl+Up / Ctrl+Down or equivalent)
- [ ] **Process management:** `pf editor` starts both servers — verify it also kills both cleanly on Ctrl+C (zombie Python processes are a common failure)
- [ ] **Monaco editor:** Loads and displays YAML — verify it loads lazily (not on the template gallery page) and does not cause SSR errors in `next build`
- [ ] **Export from editor:** PDF/PPTX download works — verify the downloaded file matches what `pf build` produces from the same YAML (export uses the editor's current in-memory YAML, not the last saved file)
- [ ] **Error state:** Invalid YAML shows error — verify the preview panel shows the last valid preview (not a blank panel) while YAML is temporarily invalid during editing

---

## Recovery Strategies (Visual Editor)

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| React layout preview components built instead of iframe | HIGH | Delete all `*Preview.tsx` layout components; implement iframe-based preview; this is a partial Phase 1 rewrite if caught late |
| Two-source state sync (YAML text + React state) | HIGH | Consolidate into single Zustand store with YAML as canonical; rewrite all form components to read from and write to the single store; affects every form component |
| Full rebuild on keystroke (no single-slide rebuild) | MEDIUM | Add `/api/build/slide/:n` endpoint to FastAPI (1–2 days); update editor to call it; debounce already in place |
| Comments stripped from user YAML on first save | LOW | Document the behavior; optionally offer `ruamel.yaml`-based save that preserves comments; no code path can fully recover already-stripped comments |
| Electron bundled prematurely | HIGH | Electron packaging adds 1–2 weeks of build pipeline work that becomes dead weight if the static-export-from-FastAPI model is adopted; remove Electron, rebuild `pf editor` CLI command |
| `react-beautiful-dnd` used for reordering | MEDIUM | Replace with `@dnd-kit/sortable`; API is similar but not identical; affects the slide panel component and all drag event handlers |

---

## Pitfall-to-Phase Mapping (Visual Editor)

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Preview fidelity divergence (React vs iframe) | Phase 1 — iframe preview architecture decision | Preview panel renders actual `slide_NN.html` from Python build, not React JSX |
| State management explosion (two sources of truth) | Phase 1 — Zustand store design | Single state update in form panel is reflected in code editor panel without `useEffect` sync |
| Rebuild latency (full build on keystroke) | Phase 2 — live preview wiring | Keystroke-to-preview-update measured at <1s for a 10-slide deck |
| Node-Python cross-process communication | Phase 1 — architecture decision | HTTP localhost calls to FastAPI; no `child_process` stdin/stdout |
| YAML comment loss on save | Phase 2 — save flow implementation | Save policy documented; user's test file retains comments across one round-trip if using code editor panel only |
| Drag-and-drop without undo | Phase 3 — slide reorder feature | Reorder is undoable (Cmd+Z restores previous order) before drag-and-drop ships |
| Desktop two-process UX | Phase 1 — `pf editor` CLI command | `pf editor` starts both processes; single Ctrl+C kills both |
| Electron/Tauri premature packaging | Phase 1 — architecture decision (deferred) | No Electron/Tauri dependency in package.json; Next.js configured for static export |

---

## Sources (Visual Editor)

- [Electron vs. Tauri comparison (DoltHub, November 2025)](https://www.dolthub.com/blog/2025-11-13-electron-vs-tauri/)
- [Tauri sidecar documentation — Python binary bundling constraints](https://v2.tauri.app/develop/sidecar/)
- [Node.js + Python IPC pitfalls (stdout buffering, line-buffering)](https://starbeamrainbowlabs.com/blog/article.php?article=posts/549-js-python-ipc.html)
- [8 Challenges Building a Complex Visual Editor in React (DEV.to)](https://dev.to/x_kernel27795/8-challenges-i-faced-building-a-complex-visual-editor-in-react-3chl)
- [dnd-kit vs react-beautiful-dnd — accessibility and maintenance status](https://www.blog.brightcoding.dev/2025/08/21/the-ultimate-drag-and-drop-toolkit-for-react-a-deep-dive-into-dnd-kit/)
- [React state management 2025 — Zustand vs Redux for undo/redo](https://makersden.io/blog/react-state-management-in-2025)
- [YAML round-trip comment preservation — Swagger Editor issue (comments stripped)](https://github.com/swagger-api/swagger-editor/issues/697)
- [ruamel.yaml round-trip parser documentation](https://yaml.dev/doc/ruamel.yaml/detail/)
- [Iframe CSP sandbox — allow-scripts + allow-same-origin security risk (Mozilla Discourse)](https://discourse.mozilla.org/t/can-someone-explain-the-issue-behind-the-rule-sandboxed-iframes-with-attributes-allow-scripts-and-allow-same-origin-are-not-allowed-for-security-reasons/110651)
- [FastAPI concurrency and race conditions (DataSci Ocean)](https://datasciocean.com/en/other/fastapi-race-condition/)
- [Live preview debounce patterns — VS Code Live Preview, YAMLResume dev mode](https://github.com/asciidoctor/asciidoctor-vscode/issues/588)
- Existing codebase analysis: `pf/mcp_server.py` (FastAPI endpoints), `pf_platform/` (platform architecture), `pf/cli.py` (Click command structure)

---
*Visual editor pitfalls research for: Presentation Framework v0.3 Visual Editor milestone*
*Researched: 2026-03-08*
