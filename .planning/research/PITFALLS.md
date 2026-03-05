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
