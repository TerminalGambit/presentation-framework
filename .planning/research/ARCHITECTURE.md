# Architecture Research

**Domain:** Extensible Python presentation engine with plugin ecosystem, LLM integration, and hosted platform
**Researched:** 2026-03-05
**Confidence:** HIGH (based on existing codebase analysis + MEDIUM for platform layer, which is greenfield)

---

## Existing Architecture (v0.2.0 Baseline)

Before documenting extension patterns, here is the actual current structure — every new component
must integrate cleanly with this baseline.

```
┌──────────────────────────────────────────────────────────────────────┐
│                         Entry Points                                  │
│  ┌────────────────┐   ┌─────────────────────────────────────────┐    │
│  │  CLI (pf)      │   │  MCP Server (pf.mcp_server)             │    │
│  │  Click groups  │   │  FastMCP / stdio JSON-RPC               │    │
│  └───────┬────────┘   └──────────────────┬──────────────────────┘    │
│          │                               │                           │
├──────────┴───────────────────────────────┴───────────────────────────┤
│                         Build Pipeline                                │
│  ┌───────────────────────────────────────────────────────────────┐   │
│  │  PresentationBuilder (pf/builder.py)                          │   │
│  │  load_config → resolve_data → validate → render → write        │   │
│  └──────┬────────────────────┬───────────────────────────────────┘   │
│         │                    │                                        │
│  ┌──────┴──────┐   ┌─────────┴──────────┐                           │
│  │ LayoutAnalyzer│  │  check_contrast    │                           │
│  │ (analyzer.py) │  │  (contrast.py)     │                           │
│  └──────────────┘  └────────────────────┘                           │
├──────────────────────────────────────────────────────────────────────┤
│                         Rendering Layer                               │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │  Jinja2 Environment                                           │    │
│  │  templates/layouts/*.html.j2  (11 layouts)                   │    │
│  │  templates/present.html.j2   (navigator shell)               │    │
│  │  theme/*.css                 (shared design tokens)           │    │
│  └──────────────────────────────────────────────────────────────┘    │
├──────────────────────────────────────────────────────────────────────┤
│                         Export Adapters                               │
│  ┌─────────────────┐   ┌──────────────────────────────────────┐      │
│  │  pdf.py          │   │  pptx.py / pptx_native.py            │      │
│  │  (Playwright)    │   │  (python-pptx + Playwright)          │      │
│  └─────────────────┘   └──────────────────────────────────────┘      │
└──────────────────────────────────────────────────────────────────────┘
```

### Data Flow (Current)

```
presentation.yaml + metrics.json
          │
          ▼
  PresentationBuilder.load_config()
  PresentationBuilder.load_metrics()
          │
          ▼
  validate_config()     ← JSON Schema (pf/schema.json)
          │
          ▼
  resolve_data()        ← {{ metrics.path }} interpolation
          │
          ▼
  LayoutAnalyzer.analyze_slide()   ← height estimation, overflow warnings
          │
          ▼
  render_slide()        ← Jinja2 template per layout
          │
          ▼
  slides/slide_NN.html  ← individual slide files
  slides/present.html   ← navigator shell (loads slides via fetch)
  slides/theme/*.css    ← copied + generated variables.css
```

---

## Target Architecture (v0.3 → v1.0)

The roadmap adds four concentric capability rings around the build pipeline.
Each ring builds on the previous and should not require modifying the core builder.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Platform Layer (v1.0)                             │
│   REST API · Hosted Viewer · Collaboration · Analytics · Embed Codes        │
├─────────────────────────────────────────────────────────────────────────────┤
│                           LLM Integration Layer (v0.5)                      │
│   Structured Schemas · Prompt→YAML · Slide Suggester · Content Optimizer   │
├─────────────────────────────────────────────────────────────────────────────┤
│                           Plugin Ecosystem (v0.4)                           │
│   Layout Plugins · Theme Plugins · Data Source Plugins · CLI Registry      │
├─────────────────────────────────────────────────────────────────────────────┤
│                       Rich Media Extensions (v0.3)                          │
│   Code Highlighting · Mermaid Diagrams · Video · Maps · Fragments           │
├─────────────────────────────────────────────────────────────────────────────┤
│                      Core Build Pipeline (v0.2 — existing)                  │
│   YAML+JSON → Jinja2 → HTML  (PresentationBuilder + LayoutAnalyzer)        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Ring 1: Rich Media Extensions (v0.3)

### Component Boundaries

Rich media is purely a **rendering-layer concern**. It touches:
- New Jinja2 layout templates (or new block types within existing layouts)
- New JS libraries loaded by `present.html.j2` (Prism, Mermaid, etc.)
- Possibly new `LayoutAnalyzer` SIZE_MODEL entries for new block types
- No changes to `PresentationBuilder` core logic required

### Component Map

| Component | File | Change Type |
|-----------|------|-------------|
| Code block renderer | `templates/layouts/*.html.j2` | Add `type: code` block handling |
| Mermaid diagram | New block type `type: mermaid` in existing layouts | Template change only |
| Video embed | New block type `type: video` | Template + new URL resolver |
| Maps embed | New block type `type: map` or new layout `map` | Template only |
| Slide fragments | `templates/present.html.j2` + JS | Navigator shell change |
| Analyzer models | `pf/analyzer.py` SIZE_MODEL dict | Add entries for new block types |

### Data Flow

```
YAML: type: code, language: python, source: "{{ metrics.snippet }}"
         │
         ▼
  resolve_data()       ← interpolates metrics.snippet
         │
         ▼
  render_slide()       ← Jinja2 code block template
         │
         ▼
  HTML: <pre class="language-python">...</pre>
         │
         ▼
  present.html loads Prism.js  ← conditional on theme.code: true flag
```

**Key decision:** Follow the existing pattern of `theme.math: true` / `theme.charts: true`
feature flags. Add `theme.code: true`, `theme.diagrams: true` etc. This keeps the output
files lean by default.

### Build Order

1. Code syntax highlighting (Prism.js — simplest, pure HTML/CSS, no runtime state)
2. Mermaid diagrams (SVG generation at runtime — needs deferred render)
3. Video embeds (YouTube/Vimeo iframe or `<video>` tag — straightforward)
4. Maps (Google Maps iframe vs static image — two-mode pattern needed for PDF export)
5. Fragments (most complex — requires presenter JS state machine changes)

---

## Ring 2: Plugin Ecosystem (v0.4)

### Architecture Pattern: Entry Points + Directory Discovery

Python's standard plugin mechanism uses `importlib.metadata` entry points defined in
`pyproject.toml`. This is how tools like pytest, Sphinx, and Babel implement plugins.

The framework should support **two discovery paths** for different user types:

```
Plugin Discovery
├── Entry Points (package plugins)
│   pyproject.toml: [project.entry-points."pf.layouts"]
│   my_layout = "my_package.layouts:MyLayout"
│   → installed via pip, discovered at runtime via importlib.metadata
│
└── Directory Discovery (local plugins)
    ~/.config/pf/plugins/layouts/   ← user-local layouts
    ./.pf/plugins/layouts/          ← project-local layouts
    → discovered by scanning for *.html.j2 + *.py metadata files
```

### Plugin Registry Component

A new `pf/registry.py` module mediates between the build pipeline and plugin sources.

```python
# pf/registry.py — component boundary

class PluginRegistry:
    """Discovers and loads layout, theme, and data source plugins."""

    def discover_layouts(self) -> dict[str, LayoutPlugin]
    def discover_themes(self) -> dict[str, ThemePlugin]
    def discover_data_sources(self) -> dict[str, DataSourcePlugin]

    def _scan_entry_points(self, group: str) -> list
    def _scan_directories(self, dirs: list[Path]) -> list
```

The `PresentationBuilder` receives a registry at construction time (dependency injection),
falling back to a default registry that only finds built-in layouts:

```python
# Modified builder constructor
class PresentationBuilder:
    def __init__(self, config_path, metrics_path, registry=None):
        self.registry = registry or PluginRegistry()
        # Jinja2 loader becomes multi-source:
        self.env = Environment(
            loader=ChoiceLoader([
                FileSystemLoader(str(TEMPLATES_DIR)),      # built-in
                *self.registry.get_template_loaders(),     # plugin layouts
            ])
        )
```

This approach preserves full backward compatibility — the builder works exactly as today
when no registry argument is passed.

### Plugin Interface Contracts

**Layout Plugin** (minimum viable contract):
```python
# A layout plugin is just:
# 1. A Jinja2 template file: {name}.html.j2
# 2. An optional Python metadata file: {name}.py
#
# The metadata file (if present) defines:
class LayoutPlugin:
    name: str              # "my-layout"
    description: str       # shown in `pf plugins list`
    size_model: dict       # for LayoutAnalyzer (block height estimation)
    schema_fragment: dict  # JSON Schema additions for validation
```

**Data Source Plugin**:
```python
class DataSourcePlugin:
    name: str              # "google-sheets"
    def fetch(self, config: dict) -> dict  # returns metrics-compatible dict
```

Data source plugins run before `resolve_data()`, enriching the metrics dict. The YAML
config gains a `sources` section:
```yaml
sources:
  - plugin: google-sheets
    sheet_id: "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms"
    range: "A1:E10"
    as: metrics.revenue_data
```

### CLI Registry Commands

New `pf plugins` subcommand group:
```
pf plugins list              # show installed + available plugins
pf plugins install <name>    # pip install + register
pf plugins remove <name>     # pip uninstall
pf plugins create layout     # scaffold a layout plugin package
```

These are thin wrappers over pip + entry point discovery — no custom registry server
needed initially.

### Component Dependencies

```
pf/registry.py          ← new, no upstream dependencies
    │
    ▼
pf/builder.py           ← receives registry via DI, no other changes needed
    │
    ▼
pf/cli.py               ← adds `pf plugins` command group
    │
    ▼
pf/mcp_server.py        ← list_layouts() reads from registry (not hardcoded dict)
```

### Build Order

1. `pf/registry.py` with entry point scanning (no UI yet)
2. Update `PresentationBuilder.__init__` to accept registry (backward-compatible)
3. Update `mcp_server.py` `list_layouts()` to use registry
4. Directory discovery (local `.pf/plugins/`)
5. `pf plugins` CLI commands
6. Data source plugin interface

---

## Ring 3: LLM Integration Layer (v0.5)

### Architecture Pattern: Schema-First LLM Interface

The key insight: the framework already has JSON Schema validation. The LLM layer should
**expose that schema as the contract** rather than building prompt engineering on top of
unstructured output.

The integration lives in two places:
1. **MCP tools** (existing server) — add new tools that LLMs call
2. **Structured output schemas** — per-layout JSON schemas that an LLM can target

```
┌──────────────────────────────────────────────────────┐
│                  LLM (any provider)                   │
│  Claude / GPT-4 / Gemini                             │
└────────────────────┬─────────────────────────────────┘
                     │ MCP protocol
                     ▼
┌──────────────────────────────────────────────────────┐
│              MCP Server (pf.mcp_server)               │
│                                                       │
│  EXISTING:                                            │
│  build_presentation()   validate_config()             │
│  list_layouts()         get_layout_example()          │
│                                                       │
│  NEW (v0.5):                                          │
│  generate_from_prompt() → returns draft YAML          │
│  suggest_layout()       → given content, picks layout │
│  optimize_slide()       → splits overflowing slide    │
│  get_layout_schema()    → machine-readable constraints│
└──────────────────────────────────────────────────────┘
```

### Component: Structured Output Schemas

Each layout gets a machine-readable schema (beyond the current JSON Schema validation)
that describes what an LLM should generate for that layout. This lives in a new
`pf/llm_schemas.py` module:

```python
# pf/llm_schemas.py
LAYOUT_SCHEMAS = {
    "two-column": {
        "description": "...",
        "generation_hints": {
            "max_left_blocks": 3,
            "max_right_blocks": 2,
            "avoid": ["more than 4 bullets per card"]
        },
        "output_schema": { ... }  # JSON Schema for LLM structured output
    }
}
```

### Component: Content Density Optimizer

The existing `LayoutAnalyzer` already estimates pixel heights. The optimizer uses this
to automatically split slides that overflow:

```
Input: slide config that exceeds USABLE_HEIGHT
         │
         ▼
  LayoutAnalyzer.estimate_column_height()
         │ (overflow detected)
         ▼
  ContentOptimizer.split_slide()
         │ (heuristic: split at block boundaries)
         ▼
  [slide_1_config, slide_2_config]  ← inserted into slides list
```

This component is **purely algorithmic** — no LLM required. It uses the size model
already in `analyzer.py`. The LLM can call it via MCP tool after generating slides.

### Data Flow: Prompt-to-Presentation

```
User prompt: "Create a 5-slide deck on Q4 revenue"
         │
         ▼
  generate_from_prompt() MCP tool
         │
         ├─ 1. Call layout suggester for each topic segment
         ├─ 2. Return structured YAML draft (not built yet)
         └─ 3. LLM reviews/edits YAML, then calls build_presentation()
         │
         ▼
  validate_config()      ← LLM checks before building
         │
         ▼
  build_presentation()   ← normal build pipeline
```

**Key constraint from PROJECT.md:** "AI content writing — engine renders, doesn't author
(LLM layer enables this externally)." The MCP tools are scaffolding tools, not content
generators. The `generate_from_prompt` tool returns a **template with placeholders** that
the calling LLM fills — it does not write the content itself.

### Build Order

1. `pf/llm_schemas.py` — per-layout structured output schemas (no dependencies)
2. `get_layout_schema()` MCP tool — exposes schemas
3. `ContentOptimizer` in `pf/optimizer.py` — algorithmic split, no LLM needed
4. `optimize_slide()` MCP tool — wraps optimizer
5. `suggest_layout()` MCP tool — layout selection heuristic based on content shape
6. `generate_from_prompt()` MCP tool — highest complexity, builds on all above

---

## Ring 4: Hosted Platform (v1.0)

### Architecture Pattern: API-First with Static File Distribution

The platform is a separate service from the CLI tool. They share the build pipeline
as a library but have different deployment models.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Client Layer                                 │
│  Browser (viewer)  |  Embed (iframe)  |  CLI  |  MCP Agents        │
└──────┬─────────────────┬──────────────────┬───────────────┬─────────┘
       │                 │                  │               │
       ▼                 ▼                  ▼               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                          API Gateway                                  │
│  FastAPI or Flask  —  /api/v1/*                                      │
│                                                                      │
│  POST /presentations/build     → triggers build, returns job ID      │
│  GET  /presentations/{id}      → returns built presentation          │
│  GET  /presentations/{id}/view → redirects to CDN-hosted viewer      │
│  POST /presentations/{id}/validate                                   │
│  GET  /layouts                 → same as MCP list_layouts            │
└────────────────────┬─────────────────────────────────────────────────┘
                     │
         ┌───────────┴──────────────┐
         ▼                          ▼
┌─────────────────┐      ┌──────────────────────────┐
│  Build Worker   │      │  Storage / CDN            │
│  (same          │      │  slides/*.html served     │
│  PresentationBuilder│  │  from object storage      │
│  as library)    │      │  (S3/R2/local filesystem)  │
└─────────────────┘      └──────────────────────────┘
         │
         ▼
┌─────────────────┐
│  Job Queue      │
│  (Redis/sqlite  │
│  for simple     │
│  deployments)   │
└─────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Notes |
|-----------|---------------|-------|
| API Gateway | Request routing, auth, job submission | FastAPI preferred — async, auto-docs, Pydantic |
| Build Worker | Runs `PresentationBuilder.build()` | Same code as CLI, different trigger |
| Job Queue | Async build coordination | Start with sqlite; Redis when scale demands |
| Storage / CDN | Hosts built slide HTML + assets | Local files for self-hosted; S3/R2 for cloud |
| Viewer | Shareable URL serving `present.html` | Existing file; no changes needed |
| Analytics | View tracking, engagement events | JS beacon in `present.html.j2` (feature-flagged) |
| Collaboration | WebSocket sync for presenter + audience cursors | Most complex; last to build |

### Platform Data Flow

```
API client POSTs config + metrics JSON
         │
         ▼
  API validates (same JSON Schema as CLI)
         │
         ▼
  Job queued with unique presentation ID
         │
         ▼
  Build worker picks up job
  Runs PresentationBuilder.build()
  Writes output to /storage/{id}/
         │
         ▼
  Job marked complete, webhook fired (optional)
         │
         ▼
  GET /presentations/{id}/view
  → serves /storage/{id}/present.html from CDN
```

### Sharing and Embed Architecture

```
Shareable URL:  https://slides.example.com/p/{short-id}
Embed code:     <iframe src="https://slides.example.com/embed/{id}"></iframe>

Embed variant of present.html:
  - No keyboard shortcuts (focus conflicts)
  - Optional auto-advance
  - Minimal chrome (no overview grid)
  - Postmessage API for host page control
```

### Collaboration Architecture (Real-Time)

Real-time sync uses a simple operational model — **presenter push, audience pull**.
This is not collaborative editing (ruled out in PROJECT.md); it's presenter state broadcast.

```
Presenter browser
   │  WebSocket (publish slide index)
   ▼
WebSocket server (simple state relay)
   │  WebSocket (subscribe to slide index)
   ▼
Audience browsers (each)
   └─ follow presenter's current slide
```

State is just an integer (current slide index) plus optional annotation coordinates.
Start with Server-Sent Events (already used for live-reload) before WebSockets — simpler
to deploy.

### Build Order

1. FastAPI skeleton with `/health` and `/layouts` endpoints (no auth, no storage)
2. File-based storage + `/presentations/build` endpoint (synchronous first, async later)
3. Shareable URL viewer (serve existing `present.html` from storage)
4. Job queue (move build to background worker)
5. Embed code variant of viewer
6. Analytics beacon (JS-only, opt-in flag in theme)
7. Collaboration (WebSocket presenter sync — last, most stateful)

---

## Recommended Project Structure (v1.0 target)

```
presentation-framework/
├── pf/                         # Core Python package (existing)
│   ├── builder.py              # PresentationBuilder (unchanged)
│   ├── analyzer.py             # LayoutAnalyzer (unchanged)
│   ├── contrast.py             # WCAG checker (unchanged)
│   ├── cli.py                  # CLI commands (adds plugins subgroup)
│   ├── mcp_server.py           # FastMCP server (adds new tools)
│   ├── schema.json             # JSON Schema (extended for new layouts)
│   │
│   ├── registry.py             # NEW v0.4 — plugin discovery
│   ├── optimizer.py            # NEW v0.5 — content density optimizer
│   ├── llm_schemas.py          # NEW v0.5 — per-layout structured schemas
│   │
│   ├── pdf.py                  # Playwright PDF (existing)
│   ├── pptx.py                 # Image-based PPTX (existing)
│   └── pptx_native.py          # Native editable PPTX (existing)
│
├── templates/                  # Jinja2 templates (existing)
│   ├── base.html.j2
│   ├── present.html.j2
│   └── layouts/                # 11 existing layouts + new rich media types
│
├── theme/                      # Shared CSS (existing)
│
├── platform/                   # NEW v1.0 — hosted service (separate process)
│   ├── api.py                  # FastAPI application
│   ├── worker.py               # Build worker (uses pf.builder as library)
│   ├── storage.py              # Storage adapter (local / S3 / R2)
│   ├── jobs.py                 # Job queue (sqlite → Redis)
│   └── templates/              # Platform-specific HTML (viewer, embed)
│
└── tests/
    ├── test_builder.py         # Existing
    ├── test_registry.py        # NEW — plugin discovery
    ├── test_optimizer.py       # NEW — content splitting
    └── test_platform/          # NEW — API integration tests
```

### Structure Rationale

- **`pf/` stays pure:** Core build pipeline must remain a pure library callable from
  CLI, MCP server, API worker, and tests. No platform dependencies leak into `pf/`.
- **`platform/` is separate:** Platform is an optional service layer. Users who only
  need the CLI never install or run it. This maps to a future `pip install pf[platform]`
  optional dependency group.
- **Registry before optimizer before LLM:** Each component has a clean dependency chain.
  Registry enables plugins. Optimizer uses existing LayoutAnalyzer. LLM schemas expose
  optimizer and registry.

---

## Architectural Patterns to Follow

### Pattern 1: Feature Flags in Theme Config

**What:** New capabilities (`theme.code: true`, `theme.diagrams: true`) load additional
JS only when needed.

**Why it works here:** The existing `theme.math: true` / `theme.charts: true` pattern
is already established and accepted by users. Extending it is zero-friction.

**Trade-offs:** Requires documentation discipline; easy to miss. But far better than
loading all libraries by default (slides would be slow and bloated).

### Pattern 2: Dependency Injection for Registry

**What:** `PresentationBuilder(registry=PluginRegistry())` — registry is passed in, not
imported globally.

**Why it works here:** Makes the builder testable without real plugin discovery. The CLI
and MCP server construct the registry before passing it. Tests pass a mock registry.

**Trade-offs:** Slightly more verbose construction site. Worth it for testability.

### Pattern 3: MCP as the LLM Integration Contract

**What:** All LLM-facing capabilities live in `mcp_server.py`. No LLM-specific logic in
the build pipeline.

**Why it works here:** The project already established MCP as the AI integration point.
This means the same tools work across Claude, GPT-4, and any MCP-compatible client
without code changes.

**Trade-offs:** MCP protocol overhead for simple tool calls. Acceptable — presentations
are not latency-sensitive.

### Pattern 4: Synchronous Build, Async Delivery (Platform)

**What:** The build pipeline stays synchronous Python. The platform wraps it in an async
job queue. Clients poll or receive webhooks.

**Why it works here:** `PresentationBuilder.build()` is inherently sequential (can't
parallelize Jinja2 renders easily). Async wrapper at the API layer is the right seam.

**Trade-offs:** Clients need polling or webhook logic. Mitigated by SSE (already used
in live-reload dev server) for real-time job status.

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Modifying the Core Builder for Each New Feature

**What people do:** Add `if layout == "mermaid"` special cases directly in `builder.py`.

**Why it's wrong:** The builder becomes a grab-bag of special cases. Plugins cannot
extend it without modifying core code. Tests become combinatorial.

**Do this instead:** All layout-specific logic lives in the Jinja2 template and the
optional `size_model` entry in `LayoutAnalyzer.SIZE_MODEL`. The builder is layout-agnostic
by design — preserve that invariant.

### Anti-Pattern 2: Hardcoding Layout List in MCP Server

**What people do:** Add new layouts to the `LAYOUT_DESCRIPTIONS` dict in `mcp_server.py`.

**Why it's wrong:** Plugin layouts would be invisible to `list_layouts()`. Users would
install a plugin and not see it in the tools.

**Do this instead:** `list_layouts()` reads from the registry, which discovers both
built-in and plugin layouts dynamically. The hardcoded dict becomes the fallback for
built-ins only.

### Anti-Pattern 3: Baking Platform Logic into the CLI

**What people do:** Add `--publish` flag to `pf build` that uploads directly.

**Why it's wrong:** Creates tight coupling between the local tool and the hosted service.
Users who don't use the platform get bloated dependencies. Auth and network errors corrupt
the local build UX.

**Do this instead:** `pf build` remains purely local. A separate `pf publish` command
or the `platform/` API handles hosting. The build artifact is just a directory of files —
publish picks up whatever `pf build` emitted.

### Anti-Pattern 4: Using Playwright for the Platform API

**What people do:** Run Playwright in the API worker for PDF generation during hosted builds.

**Why it's wrong:** Playwright is a heavy dependency with Chromium. Not suitable for
containerized API workers at scale.

**Do this instead:** The API returns the HTML build. PDF generation is either a separate
worker pool (with Playwright installed) or deferred to the client. HTML is always the
primary deliverable; PDF is an export.

---

## Integration Points

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| CLI → Builder | Direct Python call | `PresentationBuilder(config, metrics).build()` |
| MCP Server → Builder | Direct Python call (captured stdout) | Existing stdout redirect needed |
| Platform API → Builder | Direct Python call in worker process | Same pattern as MCP |
| Registry → Builder | Constructor injection | Registry passed at construction |
| LLM Schemas → MCP | Module import | `llm_schemas.LAYOUT_SCHEMAS[name]` |
| Optimizer → Analyzer | Direct call | `LayoutAnalyzer.estimate_column_height()` |
| Platform API → Storage | Storage adapter interface | Swappable local/cloud implementation |

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Google Maps (rich media) | iframe embed in template | Static image fallback for PDF export |
| YouTube/Vimeo (video) | iframe embed or `<video>` tag | No API key needed for basic embed |
| Prism.js (code highlighting) | CDN JS loaded when `theme.code: true` | Version-pin in base template |
| Mermaid.js (diagrams) | CDN JS + deferred render | Must render after DOM ready |
| Google Sheets (data source) | OAuth2 + Sheets API v4 | First data source plugin; documents the interface |
| S3/R2 (platform storage) | boto3 or Cloudflare SDK | Adapter pattern — swap without API changes |
| Redis (job queue) | redis-py | sqlite fallback for self-hosted/small deployments |

---

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| CLI only (current) | No changes — pure local file generation, no network |
| Platform 0-100 presentations/day | Single-process FastAPI, file system storage, no queue |
| Platform 100-10k/day | Add job queue (sqlite → Redis), separate build worker, S3 storage |
| Platform 10k+/day | Horizontal worker scaling, CDN for static assets, caching layer |

### Scaling Priorities

1. **First bottleneck:** Build time per presentation (Jinja2 render is fast; Playwright
   for PDF is slow). Mitigate by separating PDF generation from HTML build.
2. **Second bottleneck:** Storage I/O for large slide decks with images. Mitigate with
   CDN and object storage earlier than expected.

---

## Build Order Implications for Roadmap

The component dependency graph suggests this phase ordering is safest:

```
v0.3  Rich Media
  ├── Code highlighting   (template only, no new Python)
  ├── Mermaid             (template + theme flag)
  ├── Video embeds        (template only)
  ├── Maps                (template + export mode handling)
  └── Fragments           (navigator JS changes)

v0.4  Plugin Ecosystem
  ├── pf/registry.py      (foundation — must come first)
  ├── Builder DI update   (registry injection — minimal, backward-compat)
  ├── MCP list_layouts    (use registry, not hardcoded dict)
  ├── Directory discovery (.pf/plugins/ scanning)
  ├── pf plugins CLI      (wraps pip + registry)
  └── Data source plugins (most complex — comes last)

v0.5  LLM Integration
  ├── pf/llm_schemas.py   (pure data — no dependencies)
  ├── get_layout_schema() (trivial MCP tool wrapping schemas)
  ├── pf/optimizer.py     (uses existing LayoutAnalyzer)
  ├── optimize_slide()    (MCP tool wrapping optimizer)
  ├── suggest_layout()    (heuristic — no LLM needed)
  └── generate_from_prompt() (builds on all above)

v1.0  Platform
  ├── FastAPI skeleton    (no build, no storage — just routing)
  ├── File storage        (local fs first)
  ├── /build endpoint     (synchronous, returns output dir URL)
  ├── Shareable viewer    (serve existing present.html)
  ├── Job queue           (async builds)
  ├── Embed codes         (iframe-safe variant of present.html)
  ├── Analytics           (JS beacon — opt-in)
  └── Collaboration       (WebSocket sync — last, most stateful)
```

**Why this order:**
- Rich media before plugins — adding new block types validates the template contract that
  plugins will later use. Dogfooding before opening to external authors.
- Registry before LLM schemas — LLM tooling should be plugin-aware (can describe plugin
  layouts, not just built-ins). Building in wrong order creates a two-tier system.
- Platform last — depends on plugin ecosystem being stable enough that hosted builds
  produce the same output as local builds. Plugin instability would produce unreliable
  hosted output.

---

## Sources

- Existing codebase analysis: `pf/builder.py`, `pf/mcp_server.py`, `pf/analyzer.py`,
  `pf/cli.py`, `pf/pptx.py`, `templates/layouts/` (direct read — HIGH confidence)
- PROJECT.md requirements and constraints (direct read — HIGH confidence)
- Python entry points plugin pattern: `importlib.metadata` (training knowledge,
  well-established Python stdlib — MEDIUM confidence; verify against current packaging docs)
- FastAPI platform architecture: established pattern for async Python APIs (training
  knowledge — MEDIUM confidence)
- MCP protocol as AI integration layer: PROJECT.md decision confirmed (HIGH confidence)

---

*Architecture research for: Python presentation engine with plugin ecosystem, LLM integration, platform*
*Researched: 2026-03-05*
