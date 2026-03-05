# Stack Research

**Domain:** Python presentation engine — rich media, plugin architecture, LLM integration, hosted platform
**Researched:** 2026-03-05
**Confidence:** HIGH (all Python library versions verified via PyPI; JS library versions from training knowledge cutoff Aug 2025 — flag for spot-check before build)

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
| Plotly.js | CDN | Interactive charts |
| KaTeX | CDN | Math rendering |

---

## Recommended Stack: New Capabilities

### Rich Media — Frontend JS Libraries (CDN, no build step)

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Highlight.js | 11.x | Code syntax highlighting | Zero-config auto-detection, 190+ languages, one `<link>` + one `<script>`, themeable CSS. Prism.js requires explicit language classes and a build step for language bundles — adds friction to a YAML-driven system where users don't control markup. Highlight.js works on `<pre><code>` blocks with no attributes required. |
| Mermaid.js | 11.x | Animated diagram rendering | Native ESM CDN import, renders from text definition in `<pre class="mermaid">` blocks, matches YAML-driven philosophy. Supports flowcharts, sequence, ER, Gantt, class diagrams. v11 is the stable branch (v10 deprecated). |
| Leaflet.js | 1.9.x | Interactive maps (HTML viewer) | 42KB, no API key needed for OSM tiles, straightforward iframe-or-div embed pattern. Google Maps Embed API is an alternative but requires per-user API key management — unacceptable for an open-source CLI. Leaflet + OpenStreetMap is the zero-friction path. |
| vanilla JS fragments | n/a | Progressive slide builds | No library needed — CSS class toggling (`data-fragment-index`) with keyboard event listener in `present.html.j2`. Reveal.js pattern but implemented natively to avoid the full framework dependency. |

**Confidence:** MEDIUM — JS CDN versions from training data (Aug 2025). Verify current CDN URLs at build time for highlight.js (cdnjs.cloudflare.com/ajax/libs/highlight.js/), mermaid (cdn.jsdelivr.net/npm/mermaid/), and leaflet (unpkg.com/leaflet/).

---

### Plugin Architecture — Python

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| `importlib.metadata` entry_points | stdlib (3.10+) | Plugin discovery | The standard Python packaging mechanism since PEP 517/518. Third-party packages declare `[project.entry-points."pf.layouts"]` in their `pyproject.toml` and the engine discovers them at startup with `importlib.metadata.entry_points(group="pf.layouts")`. No runtime dependency added — it's stdlib. This is how pytest (pluggy), Sphinx, and Babel do it. |
| pluggy | 1.6.0 | Hook-based plugin invocation | pytest's plugin framework extracted as a standalone library. Use pluggy when plugins need to hook into multiple lifecycle points (pre-build, post-render, export). For simple layout/theme registration, entry_points alone is sufficient — add pluggy only if hook complexity warrants it. |
| `pathlib` directory scanning | stdlib | Local plugin discovery | For development workflows: scan `~/.config/pf/plugins/` and `./pf-plugins/` directories for Python packages that aren't installed. Enables `pf plugins install <path>` for local development plugins without pip install. |

**Rationale for NOT using a custom registry format:** Entry points are pip-native. `pip install pf-layout-mycompany` automatically registers the layout. `pip uninstall` removes it. Zero custom registry code needed for the core mechanism.

**Confidence:** HIGH — `importlib.metadata` is stdlib, pluggy is verified at 1.6.0 on PyPI.

---

### LLM Structured Output

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Pydantic | 2.12.5 | Schema definition for slide layouts | Already heavily used in Python ecosystem, FastAPI depends on it. Define one `BaseModel` per slide layout — these become both the JSON Schema for validation AND the LLM output target. |
| instructor | 1.14.5 | LLM structured output extraction | Wraps OpenAI, Anthropic, Gemini, and 10+ other providers with a unified `.chat.completions.create(response_model=MyModel)` interface. Returns typed Pydantic instances, not raw JSON. Handles retries, partial extraction, and streaming. The de facto standard for structured LLM output in Python as of 2025. |
| anthropic | 0.84.0 | Anthropic SDK (Claude) | Direct SDK for Claude models — instructor wraps this. Pin for MCP compatibility since the project already uses Claude workflows. |
| openai | 2.25.0 | OpenAI SDK (GPT-4o, o1) | Direct SDK — instructor wraps this. Required for provider-agnostic support. |

**What instructor gives us specifically:**

```python
import instructor
from anthropic import Anthropic
from pydantic import BaseModel

class TwoColumnSlide(BaseModel):
    title: str
    left: list[ContentBlock]
    right: list[ContentBlock]

client = instructor.from_anthropic(Anthropic())
slide = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=2048,
    messages=[{"role": "user", "content": "Create a slide about Q4 revenue..."}],
    response_model=TwoColumnSlide,
)
# slide is a typed TwoColumnSlide — no JSON parsing needed
```

**Confidence:** HIGH — instructor 1.14.5 and pydantic 2.12.5 verified on PyPI. Anthropic 0.84.0 and openai 2.25.0 verified.

---

### Web Platform — REST API + Hosting

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| FastAPI | 0.135.1 | REST API for build/validate/generate endpoints | Async, Pydantic-native (schema generation is automatic), auto-generates OpenAPI docs, shares the same Pydantic models as the LLM layer. The existing FastMCP server is built on a similar async foundation — FastAPI extends this naturally. Flask is synchronous and would conflict with the async WebSocket layer. |
| uvicorn | 0.41.0 | ASGI server for FastAPI | Standard pairing. `uvicorn[standard]` adds `uvloop` and `httptools` for production throughput. |
| websockets | 16.0 | Real-time collaboration sync | Stable, well-maintained WebSocket library. FastAPI has native WebSocket support using `starlette.websockets` — use that directly rather than adding `websockets` as a separate dependency, since FastAPI includes Starlette. |
| SQLAlchemy | 2.0.48 | Database ORM for platform persistence | Async-compatible (2.x), supports SQLite for development and PostgreSQL for production with no code changes. Stores presentation metadata, share tokens, view analytics. |
| Alembic | 1.18.4 | Database migrations | SQLAlchemy's official migration tool. Defines schema evolution for the platform database. |
| httpx | 0.28.1 | Async HTTP client for data source plugins | Already installed in this environment. Used for Google Sheets API, external data source plugins. Async-native — pairs with FastAPI's async model. |

**Confidence:** HIGH — all versions verified on PyPI. FastAPI at 0.135.1, uvicorn at 0.41.0, sqlalchemy at 2.0.48, alembic at 1.18.4, httpx at 0.28.1.

---

### Hosted Platform — Storage and Deployment

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| boto3 | 1.42.x | S3-compatible file storage | Store built slide HTML bundles. Compatible with AWS S3, Cloudflare R2, Backblaze B2, and MinIO (local dev). Don't lock to a single provider — use the S3 API interface. |
| SQLite (dev) / PostgreSQL (prod) | — | Platform database | SQLite for zero-config local development. PostgreSQL for production. SQLAlchemy 2.x handles both transparently. |

**Deployment target:** Railway, Render, or Fly.io for the hosted platform — all support Python + PostgreSQL + Dockerfile deploys. Avoid AWS-first lock-in given the open-source nature of the project.

**Confidence:** MEDIUM — deployment platform recommendations are based on ecosystem patterns as of Aug 2025. Verify current pricing/free-tier availability before choosing.

---

## Installation

```bash
# Rich media — no Python packages needed (CDN-only JS)
# Mermaid, Highlight.js, and Leaflet are injected via Jinja2 templates
# when theme.diagrams, theme.code, or theme.maps are enabled

# Plugin architecture — stdlib only for entry_points discovery
# pluggy only if hook complexity warrants it:
pip install pluggy>=1.6.0

# LLM structured output
pip install "instructor>=1.14.0" "pydantic>=2.12.0"
# LLM provider SDKs (install only what users need)
pip install "anthropic>=0.84.0"   # for Claude
pip install "openai>=2.25.0"      # for GPT-4o / o1

# Web platform API
pip install "fastapi>=0.135.0" "uvicorn[standard]>=0.41.0"
pip install "sqlalchemy>=2.0.48" "alembic>=1.18.0"
pip install "httpx>=0.28.0"

# Platform storage
pip install "boto3>=1.42.0"
```

**pyproject.toml extras_require additions:**

```toml
[project.optional-dependencies]
llm = ["instructor>=1.14.0", "pydantic>=2.12.0", "anthropic>=0.84.0", "openai>=2.25.0"]
platform = ["fastapi>=0.135.0", "uvicorn[standard]>=0.41.0", "sqlalchemy>=2.0.48", "alembic>=1.18.0", "httpx>=0.28.0", "boto3>=1.42.0"]
```

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Highlight.js (CDN) | Prism.js | Use Prism if the project gains a build pipeline and needs line numbers, copy buttons, or diff highlighting — Prism's plugin ecosystem is richer but requires explicit language registration |
| Mermaid.js 11.x | D3.js or Graphviz | Use D3 if custom force-directed graphs or complex data visualizations are needed beyond Mermaid's diagram types |
| Leaflet + OSM | Google Maps Embed | Use Google Maps only if users consistently need Street View, business listings, or custom styled maps — requires API key management, not appropriate for CLI default |
| instructor | LangChain | Use LangChain if the LLM layer needs chains, agents, and retrieval augmentation. For structured output from a fixed schema (our use case), instructor is dramatically simpler — 5 lines vs 50 |
| FastAPI | Flask | Use Flask if the team needs synchronous request handling only and wants simpler deployment. FastAPI is the right choice here because WebSocket support and Pydantic model integration are needed |
| SQLAlchemy 2.x async | Tortoise ORM or SQLModel | Use SQLModel if a lighter-weight ORM with direct Pydantic integration is desired — it wraps SQLAlchemy anyway, so no real benefit over raw SQLAlchemy 2.x |
| importlib.metadata entry_points | Custom plugin registry | Use a custom registry only if pip-based installation is not the distribution model (e.g., browser plugins). For Python packages, entry_points is always correct |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| reveal.js as a rendering engine | Would require migrating the existing HTML template system — the current Jinja2 + vanilla JS system is already functional and presentation-framework-specific. reveal.js solves problems we've already solved | Continue with the existing template system; add Mermaid/Highlight.js as opt-in CDN layers |
| LangChain for structured output | 10x the dependency surface area for a problem that instructor solves with one decorator. LangChain v0.3+ improved but is still framework-heavy | instructor |
| Pydantic v1 | v1 is in maintenance mode, v2 is 5-20x faster due to Rust core, and instructor 1.x requires Pydantic v2. No reason to use v1 in a new codebase | Pydantic 2.12.x |
| Django for the platform API | Full MVC framework adds ORM, admin, auth, templates — most of which conflict with or duplicate the existing system. The platform needs a thin API layer, not a web framework | FastAPI |
| Celery for async builds | Adds Redis/RabbitMQ broker dependency for what should be a stateless build process. FastAPI's `BackgroundTasks` or Python's `asyncio` is sufficient for presentation build jobs | FastAPI BackgroundTasks |
| WebSockets via a separate websockets library | FastAPI includes Starlette's WebSocket support natively — adding the `websockets` package separately creates version conflicts | `from fastapi import WebSocket` |
| PyWebview or Electron for a desktop wrapper | Out of scope per PROJECT.md — web-first only | — |

---

## Stack Patterns by Variant

**If rich media only (v0.3 milestone):**
- Add Highlight.js, Mermaid.js, Leaflet via conditional template injection (`{% if theme.code %}`, `{% if theme.diagrams %}`, `{% if theme.maps %}`)
- No new Python dependencies
- Fragment animation via vanilla JS in `present.html.j2`

**If plugin system only (v0.4 milestone):**
- Use `importlib.metadata.entry_points(group="pf.layouts")` — stdlib, zero new deps
- Add pluggy only when hook complexity exceeds simple registration
- Build `pf plugins list` / `pf plugins install` CLI commands on top of pip subprocess calls

**If LLM integration only (v0.5 milestone):**
- `pip install pf[llm]` installs instructor + pydantic + provider SDKs
- One Pydantic model per layout, derived from the existing `schema.json`
- New MCP tool `generate_presentation(prompt, theme, slide_count)` added to `mcp_server.py`

**If hosted platform only (v0.7+ milestone):**
- FastAPI app lives in `pf/api/` directory, separate from CLI
- SQLite for local dev (`pf platform serve`), PostgreSQL for production deployment
- Build pipeline runs the existing `PresentationBuilder` as a FastAPI background task

---

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| instructor 1.14.x | pydantic 2.x (required) | instructor 1.x drops pydantic v1 support entirely |
| instructor 1.14.x | anthropic 0.84.x | instructor wraps the Anthropic client; keep anthropic updated with instructor releases |
| FastAPI 0.135.x | pydantic 2.x | FastAPI 0.100+ requires pydantic v2 |
| FastAPI 0.135.x | SQLAlchemy 2.0.x | No direct dependency but async session patterns require SA 2.x |
| SQLAlchemy 2.0.x | alembic 1.18.x | Always keep alembic in sync with SQLAlchemy major version |
| mcp[cli] 1.6+ | fastmcp 3.1.0 | Project uses `mcp.server.fastmcp.FastMCP` — fastmcp 3.x is the refactored version; verify import path before upgrading |

---

## Sources

- PyPI `pip index versions` — verified versions for: instructor (1.14.5), pydantic (2.12.5), fastapi (0.135.1), uvicorn (0.41.0), sqlalchemy (2.0.48), alembic (1.18.4), httpx (0.28.1), websockets (16.0), boto3 (1.42.62), pluggy (1.6.0), anthropic (0.84.0), openai (2.25.0), fastmcp (3.1.0), python-pptx (1.0.2) — HIGH confidence
- Existing `setup.py` — confirmed current dependency pinning in v0.2.0 — HIGH confidence
- `pf/mcp_server.py` — confirmed FastMCP import pattern (`from mcp.server.fastmcp import FastMCP`) — HIGH confidence
- JS library versions (Highlight.js 11.x, Mermaid.js 11.x, Leaflet 1.9.x) — training knowledge cutoff Aug 2025, CDN available — MEDIUM confidence, verify CDN URLs before implementing
- Python Packaging Guide (packaging.python.org/en/latest/guides/creating-and-discovering-plugins/) — entry_points pattern — HIGH confidence (stdlib, well-documented)
- instructor project patterns — training knowledge through Aug 2025, confirmed active development by version history on PyPI — HIGH confidence

---

*Stack research for: presentation-framework rich media, plugins, LLM, platform*
*Researched: 2026-03-05*
