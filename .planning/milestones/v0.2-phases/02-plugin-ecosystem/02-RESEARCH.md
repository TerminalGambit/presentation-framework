# Phase 2: Plugin Ecosystem - Research

**Researched:** 2026-03-06
**Domain:** Python plugin architecture — entry points, Jinja2 template extension, CSS isolation, data source adapters, CLI extensibility
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PLUG-01 | Developer can create and register custom layout plugins via Python entry points or `layouts/` directory | Entry points (importlib.metadata) + directory scan fallback; ChoiceLoader for template discovery |
| PLUG-02 | Developer can create and distribute installable theme packages (`pip install pf-theme-<name>`) | Entry points group `pf.themes`; theme discovery pattern identical to layouts |
| PLUG-03 | Developer can create data source plugins connecting to Google Sheets, REST APIs, and databases | gspread service_account_from_dict for Sheets; requests for REST; credential-from-env pattern |
| PLUG-04 | User can discover and install plugins via CLI (`pf plugins list`, `pf plugins install <name>`) | Click nested group (`@cli.group()`); pip subprocess for install; importlib.metadata for list |
| PLUG-05 | Layout plugins support template inheritance (base layout → variant pattern) | Jinja2 `{% extends %}` with ChoiceLoader; plugin templates register under known name |
| PLUG-06 | Plugin CSS is isolated to prevent style leaks into core slides or other plugins | CSS class-prefix scoping: `.pf-layout-<plugin-name>` wrapper; injected inline per slide |
</phase_requirements>

---

## Summary

Phase 2 introduces a plugin ecosystem so developers can extend the presentation framework with custom layouts, themes, and data sources without touching core code. The Python entry points mechanism (via `importlib.metadata`, stdlib since Python 3.10) is the standard way to achieve this — it is exactly the pattern used by pytest plugins, Flask extensions, and stevedore. A second discovery path (scanning a local `layouts/` directory in the project) provides a developer-friendly fallback for in-progress work that is not yet pip-installed.

The Jinja2 `ChoiceLoader` (accepts an ordered list of loaders) is the correct tool for merging plugin template directories with the core `templates/` directory. Plugin templates placed earlier in the loader list override core templates; plugin templates placed later provide additions. CSS isolation can be achieved without Shadow DOM by requiring each plugin layout to wrap its root element with a unique class (`.pf-layout-<name>`) and scoping all plugin CSS to that selector. Data source plugins follow the adapter pattern: each exposes a `fetch(config: dict) -> dict` callable registered under the `pf.datasources` entry-point group; credential values are read from environment variables or a local `.pf/credentials.json` file, never from YAML.

**Primary recommendation:** Use `importlib.metadata.entry_points(group='pf.layouts')` as the authoritative plugin mechanism, augmented with directory scanning for local development. Build `pf/registry.py` as a thin, backward-compatible layer that the builder consumes. Schema validation is relaxed to `additionalProperties: true` for plugin-supplied layouts (per the locked Phase 2 decision in STATE.md).

---

## Standard Stack

### Core (already in project)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `importlib.metadata` | stdlib (Python 3.10+) | Entry point discovery | Standard library; replaces deprecated `pkg_resources` |
| `Jinja2` | >=3.0 | Template engine | Already used; `ChoiceLoader` enables plugin template overlay |
| `click` | >=8.0 | CLI command groups | Already used; `@cli.group()` creates the `pf plugins` subgroup |

### Plugin Dependencies (pip install on demand)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `gspread` | >=6.0 | Google Sheets data source | PLUG-03: Sheets adapter plugin |
| `requests` | >=2.31 | REST API data source | PLUG-03: REST adapter plugin |
| `python-dotenv` | >=1.0 | `.env` credential loading | Plugin dev convenience; not a core dep |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `importlib.metadata` (stdlib) | `stevedore` (OpenStack library) | stevedore adds manager abstractions on top of entry points; not needed for this project's simplicity goals. Stay with stdlib. |
| `importlib.metadata` | `pkg_resources` | `pkg_resources` is deprecated as of setuptools 67+; do not use |
| CSS class-prefix scoping | Shadow DOM | Shadow DOM requires custom elements / JS; class-prefix scoping works with vanilla CSS and static HTML — matches the project's no-framework philosophy |
| `gspread` | `google-api-python-client` directly | gspread is a simpler wrapper that handles auth and sheet access; preferred for data source plugins |

**Installation for development:**
```bash
# No new core deps — importlib.metadata is stdlib in Python 3.10+
# Optional plugin extras:
pip install gspread>=6.0 requests>=2.31
```

---

## Architecture Patterns

### Recommended Project Structure (new files)
```
pf/
├── registry.py          # PluginRegistry — entry point discovery + dir scanning
├── cli.py               # Add @cli.group('plugins') with list/install/info subcommands
├── builder.py           # Modify: inject registry into __init__, use ChoiceLoader
└── schema.json          # Relax layout enum to allow additionalProperties: true

templates/
└── layouts/             # Core layouts unchanged

# Plugin package example (external, pip-installable):
pf_layout_kanban/
├── pyproject.toml       # [project.entry-points."pf.layouts"] kanban = "pf_layout_kanban:plugin"
├── pf_layout_kanban/
│   ├── __init__.py      # plugin = LayoutPlugin(name='kanban', ...)
│   └── templates/
│       └── kanban.html.j2
└── static/
    └── kanban.css       # Scoped with .pf-layout-kanban { ... }
```

### Pattern 1: PluginRegistry — Entry Point + Directory Discovery

**What:** A single registry class that discovers plugins from two sources in priority order: (1) pip-installed packages via `pf.layouts` entry point group, (2) a local `layouts/` directory in the working directory (for dev).

**When to use:** Called once at builder startup; result cached for the build lifetime.

**Example:**
```python
# pf/registry.py
# Source: https://docs.python.org/3/library/importlib.metadata.html
from importlib.metadata import entry_points
from pathlib import Path
from jinja2 import ChoiceLoader, FileSystemLoader


class PluginRegistry:
    def __init__(self):
        self._layouts: dict[str, "LayoutPlugin"] = {}
        self._themes: dict[str, "ThemePlugin"] = {}
        self._datasources: dict[str, "DataSourcePlugin"] = {}

    def discover(self, project_dir: Path | None = None) -> None:
        """Discover all plugins. Call once before build."""
        self._discover_layouts(project_dir)
        self._discover_themes(project_dir)
        self._discover_datasources()

    def _discover_layouts(self, project_dir: Path | None) -> None:
        # 1. Entry points (pip-installed packages)
        for ep in entry_points(group="pf.layouts"):
            try:
                plugin = ep.load()
                self._layouts[plugin.name] = plugin
            except Exception as exc:
                import warnings
                warnings.warn(f"Failed to load layout plugin '{ep.name}': {exc}")

        # 2. Local directory fallback (developer workflow)
        if project_dir:
            local_layouts_dir = project_dir / "layouts"
            if local_layouts_dir.is_dir():
                for template_file in local_layouts_dir.glob("*.html.j2"):
                    name = template_file.stem.replace(".html", "")
                    # Auto-register as a local plugin (no Python class needed)
                    self._layouts[name] = LocalLayoutPlugin(
                        name=name, template_path=template_file
                    )

    @property
    def layout_names(self) -> list[str]:
        return list(self._layouts.keys())

    def get_template_loader(self, core_templates_dir: Path) -> ChoiceLoader:
        """
        Build a ChoiceLoader: plugin templates first, core templates last.
        Plugin templates can override core templates by matching filename.
        """
        loaders = []
        for plugin in self._layouts.values():
            if hasattr(plugin, "templates_dir") and plugin.templates_dir:
                loaders.append(FileSystemLoader(str(plugin.templates_dir)))
        loaders.append(FileSystemLoader(str(core_templates_dir)))
        return ChoiceLoader(loaders)
```

### Pattern 2: LayoutPlugin Contract

**What:** A minimal Python class that plugin developers implement. The contract is small to minimize maintenance burden.

**When to use:** Every pip-installable layout plugin implements this.

**Example:**
```python
# Plugin developer's package: pf_layout_kanban/__init__.py
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class LayoutPlugin:
    name: str                          # matches the .html.j2 stem
    description: str = ""
    templates_dir: Path | None = None  # dir containing {name}.html.j2
    css_files: list[Path] = field(default_factory=list)
    version: str = "0.0.0"


# The entry point callable must be an instance or a factory
plugin = LayoutPlugin(
    name="kanban",
    description="Kanban board layout",
    templates_dir=Path(__file__).parent / "templates",
    css_files=[Path(__file__).parent / "static" / "kanban.css"],
)
```

Plugin's `pyproject.toml`:
```toml
[project.entry-points."pf.layouts"]
kanban = "pf_layout_kanban:plugin"
```

### Pattern 3: Theme Plugin

**What:** Installable theme packages expose a `ThemePlugin` under the `pf.themes` entry point group. The builder resolves the theme by name from the `presentation.yaml` `theme.name` key.

**When to use:** User writes `theme: {name: "corporate-blue", accent: "#0055A4"}` and the named theme supplies default values; user values override.

**Example:**
```python
# pf/registry.py — theme discovery
for ep in entry_points(group="pf.themes"):
    plugin = ep.load()
    self._themes[plugin.name] = plugin

# In builder.generate_variables_css():
if theme_name := theme_cfg.get("name"):
    if base_theme := registry.get_theme(theme_name):
        # Merge: base defaults < presentation.yaml overrides
        merged = {**base_theme.defaults, **theme_cfg}
```

Plugin's `pyproject.toml`:
```toml
[project.entry-points."pf.themes"]
corporate-blue = "pf_theme_corporate_blue:plugin"
```

### Pattern 4: Data Source Plugin

**What:** Plugins expose a `fetch(config: dict, credentials: dict) -> dict` function under `pf.datasources`. The builder resolves datasource references from `metrics.json` or from `presentation.yaml` `datasources:` key.

**When to use:** User wants metrics pulled from Google Sheets or a REST API at build time.

**Example:**
```python
# pf_datasource_sheets/__init__.py
import gspread
import json
import os


def fetch(config: dict, credentials: dict) -> dict:
    """
    Fetch data from a Google Sheet and return as a metrics dict.
    Credentials resolved in order:
      1. credentials dict passed in (from .pf/credentials.json or env vars)
      2. GOOGLE_APPLICATION_CREDENTIALS env var path
      3. ~/.config/gspread/service_account.json (gspread default)
    """
    if credentials.get("google_service_account"):
        creds_dict = json.loads(credentials["google_service_account"])
        gc = gspread.service_account_from_dict(creds_dict)
    elif os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        gc = gspread.service_account()   # reads GOOGLE_APPLICATION_CREDENTIALS
    else:
        gc = gspread.service_account()   # gspread default path

    sheet_id = config["sheet_id"]
    worksheet_name = config.get("worksheet", "Sheet1")
    sh = gc.open_by_key(sheet_id)
    ws = sh.worksheet(worksheet_name)
    return {"rows": ws.get_all_records()}
```

Plugin's `pyproject.toml`:
```toml
[project.entry-points."pf.datasources"]
sheets = "pf_datasource_sheets:fetch"
```

### Pattern 5: `pf plugins` CLI Group

**What:** A Click command group nested under the main `cli` group.

**When to use:** Users run `pf plugins list` or `pf plugins install pf-layout-kanban`.

**Example:**
```python
# pf/cli.py — add after existing commands
import subprocess
from pf.registry import PluginRegistry


@cli.group()
def plugins():
    """Manage presentation framework plugins."""
    pass


@plugins.command(name="list")
def plugins_list():
    """List installed plugins."""
    registry = PluginRegistry()
    registry.discover()

    layouts = registry.layout_names
    themes = registry.theme_names
    datasources = registry.datasource_names

    click.echo(click.style("Installed Plugins", bold=True))
    click.echo(f"\n  Layouts ({len(layouts)}):")
    for name in sorted(layouts):
        click.echo(f"    - {name}")
    click.echo(f"\n  Themes ({len(themes)}):")
    for name in sorted(themes):
        click.echo(f"    - {name}")
    click.echo(f"\n  Data Sources ({len(datasources)}):")
    for name in sorted(datasources):
        click.echo(f"    - {name}")


@plugins.command(name="install")
@click.argument("package")
def plugins_install(package: str):
    """Install a plugin package from PyPI."""
    click.echo(f"Installing {package}...")
    result = subprocess.run(
        ["pip", "install", package], capture_output=True, text=True
    )
    if result.returncode == 0:
        click.echo(click.style(f"  Installed {package}", fg="green"))
    else:
        click.echo(click.style(f"  Install failed:\n{result.stderr}", fg="red"), err=True)
        raise SystemExit(1)


@plugins.command(name="info")
@click.argument("plugin_name")
def plugins_info(plugin_name: str):
    """Show information about a specific plugin."""
    registry = PluginRegistry()
    registry.discover()
    # ... look up and display plugin metadata
```

### Pattern 6: CSS Isolation via Class Prefix

**What:** Every plugin layout wraps its root element with a unique class `.pf-layout-{name}`. All plugin CSS is scoped to that class.

**When to use:** Every layout plugin that ships CSS.

**Example:**
```html
<!-- pf_layout_kanban/templates/kanban.html.j2 -->
<div class="slide pf-layout-kanban" data-density="{{ density }}">
  <!-- layout HTML here -->
</div>
```

```css
/* pf_layout_kanban/static/kanban.css — ALL rules scoped */
.pf-layout-kanban .kanban-board { display: grid; }
.pf-layout-kanban .kanban-column { min-width: 200px; }
/* Never: .kanban-board { } — this leaks to core slides */
```

The builder injects plugin CSS inline (in the slide's `<head>`) or copies to the output `theme/plugins/` directory during build.

### Anti-Patterns to Avoid

- **Modifying `render_slide()` for plugin layouts:** The registry's `ChoiceLoader` handles template dispatch transparently — `render_slide()` stays unchanged, calling `env.get_template(f"layouts/{layout}.html.j2")` works for both core and plugin templates because the plugin's `templates/layouts/` dir is on the loader path.
- **Plugin schemas with `additionalProperties: false`:** Per the STATE.md decision, plugin layouts must use `additionalProperties: true` to avoid breaking existing YAML configs.
- **Loading all plugins eagerly:** Wrap every `ep.load()` call in try/except and emit a warning — a broken plugin should not fail the build.
- **Storing credentials in metrics.json or presentation.yaml:** Credentials must only come from environment variables or a git-ignored `.pf/credentials.json`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Plugin discovery | Custom file scanning or import hackery | `importlib.metadata.entry_points()` | Standard library; handles all edge cases of installed vs editable packages |
| Credential storage | Custom encryption or YAML fields | Environment variables + `gspread.service_account_from_dict()` | Security best practice; gspread handles the auth flow |
| Template overlay | Custom template loader | Jinja2 `ChoiceLoader` | Built-in, correct priority semantics, tested |
| Plugin install | Custom download/extract | `subprocess.run(["pip", "install", package])` | pip handles deps, version conflicts, editable installs |
| CSS namespace isolation | Shadow DOM or iframe sandboxing | CSS class prefix scoping | Matches static HTML output model; no JS overhead |

**Key insight:** The entry points mechanism was designed exactly for this use case — pytest, Sphinx, Flask extensions, and most major Python frameworks all use it. Building a custom mechanism would re-create these semantics with more bugs and less ecosystem support.

---

## Common Pitfalls

### Pitfall 1: Schema Validation Rejects Plugin Layout Names
**What goes wrong:** The current `schema.json` has `"layout": {"type": "string", "enum": [...]}` — any plugin layout name fails validation before the build even starts.
**Why it happens:** The enum list is hardcoded to core layout names.
**How to avoid:** Change the `layout` property to `{"type": "string"}` (remove `enum`). Add a separate runtime check in `render_slide()` that emits a friendly error including plugin layouts in the "valid layouts" list.
**Warning signs:** Build fails with `layout: 'kanban' is not one of [...]` for a properly installed plugin.

### Pitfall 2: Entry Points Not Refreshed After `pip install -e .`
**What goes wrong:** Developer installs their plugin with `pip install -e .` but `entry_points()` returns nothing.
**Why it happens:** Editable installs in modern pip (PEP 660) write a `.dist-info/direct_url.json` but entry points registration requires the build backend to have written the metadata. Some older setups miss this.
**How to avoid:** Test with `pip install -e ".[dev]"` and verify with `python -c "from importlib.metadata import entry_points; print(list(entry_points(group='pf.layouts')))"`.
**Warning signs:** `pf plugins list` shows no plugins despite `pip list` showing the package.

### Pitfall 3: ChoiceLoader Picks Wrong Template
**What goes wrong:** A plugin ships a template named `two-column.html.j2` (matching a core layout name). The plugin's version overrides the core layout for all users.
**Why it happens:** ChoiceLoader returns the first match; plugin loaders are prepended.
**How to avoid:** Plugin templates must live under `templates/layouts/` with unique names. Validate uniqueness in registry.discover() and warn on collision.
**Warning signs:** Core slides suddenly have wrong rendering after plugin install.

### Pitfall 4: Plugin CSS Leaks Into Core Slides
**What goes wrong:** Plugin CSS rule `.card { border: 3px solid red; }` changes appearance of all `two-column` slides that use `.card` blocks.
**Why it happens:** Plugin CSS was not scoped to the layout's root class.
**How to avoid:** Require `.pf-layout-{name}` wrapper in template; enforce in review/documentation. Validator in `pf plugins info` can warn if CSS contains unscoped rules.
**Warning signs:** Core slides change appearance after plugin install; contrast with a presentation that has no plugin slides.

### Pitfall 5: Data Source Plugin Fails Silently on Missing Credentials
**What goes wrong:** `fetch()` is called but `GOOGLE_SHEETS_CREDENTIALS` env var is missing; the plugin returns an empty dict instead of raising an error.
**Why it happens:** Plugin swallows exceptions trying to be resilient.
**How to avoid:** Data source plugins MUST raise `PluginCredentialError` (a custom exception from `pf.registry`) if credentials are absent. Builder catches this and emits a clear error message.
**Warning signs:** Metrics dict is empty; `{{ metrics.x }}` appears as literal text in slides.

### Pitfall 6: `pf plugins install` Invokes Wrong `pip`
**What goes wrong:** `subprocess.run(["pip", "install", ...])` uses a different pip than the active virtual environment.
**How to avoid:** Use `[sys.executable, "-m", "pip", "install", ...]` to guarantee the pip that belongs to the running Python interpreter.
**Warning signs:** Package installs but `pf plugins list` doesn't show it (different Python env).

---

## Code Examples

### Verifying Entry Points Discovery
```python
# Source: https://docs.python.org/3/library/importlib.metadata.html
from importlib.metadata import entry_points

# All layout plugins
layout_eps = entry_points(group="pf.layouts")
for ep in layout_eps:
    print(f"  {ep.name}: {ep.value}")
    plugin = ep.load()   # imports the module, returns the registered object
```

### Minimal pyproject.toml for a Layout Plugin
```toml
# pf-layout-kanban/pyproject.toml
[build-system]
requires = ["setuptools>=61"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "pf-layout-kanban"
version = "0.1.0"
dependencies = []  # pf is NOT a hard dep — avoids circular installs

[project.entry-points."pf.layouts"]
kanban = "pf_layout_kanban:plugin"
```

### Builder Integration (backward-compatible)
```python
# pf/builder.py — modified __init__
from pf.registry import PluginRegistry

class PresentationBuilder:
    def __init__(self, config_path="presentation.yaml", metrics_path="metrics.json",
                 registry: PluginRegistry | None = None):
        self.config_path = Path(config_path)
        self.metrics_path = Path(metrics_path)
        self._registry = registry or PluginRegistry()
        self._registry.discover(project_dir=self.config_path.parent)

        self.env = Environment(
            loader=self._registry.get_template_loader(TEMPLATES_DIR),
            autoescape=False,
        )
```

### CSS Scoping Pattern
```css
/* CORRECT — all rules scoped */
.pf-layout-kanban {
  --kanban-col-width: 280px;
}
.pf-layout-kanban .board { display: flex; gap: 1rem; }
.pf-layout-kanban .column { width: var(--kanban-col-width); }

/* WRONG — leaks globally */
.board { display: flex; }
```

### gspread Credential Resolution (env var preferred)
```python
# Source: https://docs.gspread.org/en/latest/oauth2.html
import gspread, os, json

def _build_gc():
    raw = os.environ.get("PF_GOOGLE_SERVICE_ACCOUNT")
    if raw:
        return gspread.service_account_from_dict(json.loads(raw))
    creds_file = Path.home() / ".config" / "gspread" / "service_account.json"
    if creds_file.exists():
        return gspread.service_account(filename=str(creds_file))
    raise PluginCredentialError(
        "Google Sheets plugin requires PF_GOOGLE_SERVICE_ACCOUNT env var "
        "or ~/.config/gspread/service_account.json"
    )
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `pkg_resources.iter_entry_points()` | `importlib.metadata.entry_points(group=...)` | Python 3.10 / setuptools 67+ | `pkg_resources` deprecated; stdlib version is faster and has no extra deps |
| Manual plugin scanning with `importlib.import_module()` | Entry points via `pyproject.toml` | ~2022 (PEP 517/518 era) | Standard mechanism; pip/pipx/uv all understand it |
| Single `FileSystemLoader` | `ChoiceLoader([plugin_loader, core_loader])` | Jinja2 2.x (stable) | Enables transparent template override without modifying builder |

**Deprecated / outdated:**
- `pkg_resources`: Do not use. Replaced by `importlib.metadata` (stdlib).
- `setup.py` with `entry_points={}`: Still works but `pyproject.toml` is the current standard for new plugin packages.
- `MANIFEST.in` for including template files: Use `package_data` in `pyproject.toml` or `[tool.setuptools.package-data]`.

---

## Open Questions

1. **Plugin registry file for `pf plugins list --available`**
   - What we know: PyPI supports querying packages by naming convention (`pf-layout-*`, `pf-theme-*`) via the simple index API
   - What's unclear: Whether to implement a curated registry JSON file (hosted on GitHub) or rely on PyPI naming convention search
   - Recommendation: For PLUG-04, scope to "list installed" + "install by name from PyPI." A curated registry is MARKET-01 scope (v2).

2. **Data source plugin invocation timing**
   - What we know: Data source plugins must run before `resolve_data()` so metrics are populated
   - What's unclear: Whether the `presentation.yaml` should declare `datasources:` at the top level, or whether `metrics.json` itself can reference plugin calls
   - Recommendation: Add an optional `datasources:` key to `presentation.yaml` (top level). Builder resolves datasources first, merges result into `self.metrics`, then `resolve_data()` runs as before.

3. **CSS injection method for plugin styles**
   - What we know: Plugin CSS must be present in the output; slides are individual HTML files
   - What's unclear: Whether to (a) copy plugin CSS to `slides/theme/plugins/` and `<link>` it from base.html.j2, or (b) inject it inline per slide
   - Recommendation: Option (a) — copy to `slides/theme/plugins/{plugin_name}.css` and add a `<link>` tag in `base.html.j2` for each detected plugin layout. This avoids duplicating large CSS in every slide file.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (already installed) |
| Config file | None — uses default discovery |
| Quick run command | `pytest tests/test_registry.py -x` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PLUG-01 | Entry point layout discovery loads plugin template | unit | `pytest tests/test_registry.py::test_layout_discovery_via_entry_points -x` | Wave 0 |
| PLUG-01 | Local `layouts/` directory scan adds plugin to registry | unit | `pytest tests/test_registry.py::test_local_directory_discovery -x` | Wave 0 |
| PLUG-01 | Builder uses ChoiceLoader with plugin templates | unit | `pytest tests/test_registry.py::test_builder_uses_choice_loader -x` | Wave 0 |
| PLUG-02 | Theme entry point discovery loads theme plugin | unit | `pytest tests/test_registry.py::test_theme_discovery -x` | Wave 0 |
| PLUG-02 | Theme defaults merged with presentation.yaml overrides | unit | `pytest tests/test_builder.py::test_theme_plugin_merge -x` | Wave 0 |
| PLUG-03 | Data source fetch() called and merged into metrics | unit | `pytest tests/test_datasources.py::test_datasource_fetch_merges_metrics -x` | Wave 0 |
| PLUG-03 | Missing credentials raises PluginCredentialError | unit | `pytest tests/test_datasources.py::test_missing_credentials_raises -x` | Wave 0 |
| PLUG-04 | `pf plugins list` shows installed plugins | unit | `pytest tests/test_cli.py::test_plugins_list -x` | Wave 0 |
| PLUG-04 | `pf plugins install` calls pip with correct args | unit | `pytest tests/test_cli.py::test_plugins_install -x` | Wave 0 |
| PLUG-05 | Plugin template with `{% extends "layouts/two-column.html.j2" %}` renders correctly | unit | `pytest tests/test_registry.py::test_template_inheritance -x` | Wave 0 |
| PLUG-06 | Plugin CSS file copied to output `theme/plugins/` | unit | `pytest tests/test_registry.py::test_css_injection -x` | Wave 0 |
| PLUG-06 | Core slides unaffected when plugin layout is in same deck | integration | `pytest tests/test_registry.py::test_css_isolation -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_registry.py -x`
- **Per wave merge:** `pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_registry.py` — covers PLUG-01, PLUG-02, PLUG-05, PLUG-06
- [ ] `tests/test_datasources.py` — covers PLUG-03
- [ ] `tests/test_cli.py` — covers PLUG-04 (may extend existing `test_main.py`)
- [ ] `pf/registry.py` — core registry module (does not exist yet)

*(No framework install needed — pytest already present)*

---

## Sources

### Primary (HIGH confidence)
- `https://docs.python.org/3/library/importlib.metadata.html` — `entry_points()` API, group parameter, `.load()` method, version compatibility
- `https://setuptools.pypa.io/en/latest/userguide/entry_point.html` — entry point definition in setup.py and pyproject.toml
- `https://packaging.python.org/en/latest/guides/creating-and-discovering-plugins/` — Three plugin discovery patterns (entry points recommended)
- `https://jinja.palletsprojects.com/en/stable/api/` — `ChoiceLoader`, `FileSystemLoader` with multiple paths, resolution order

### Secondary (MEDIUM confidence)
- `https://docs.gspread.org/en/latest/oauth2.html` — gspread authentication: `service_account()`, `service_account_from_dict()`, credential resolution
- `https://click.palletsprojects.com/en/stable/commands-and-groups/` — Click group nesting for `pf plugins` subcommand group

### Tertiary (LOW confidence)
- Community patterns for CSS class-prefix isolation (verified against project's static HTML output model — no Counter-evidence found in official docs)

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — `importlib.metadata` is stdlib; Jinja2 `ChoiceLoader` is documented API
- Architecture: HIGH — entry points pattern validated against Python Packaging User Guide official docs
- Pitfalls: MEDIUM — entry point edge cases (editable installs, env mismatch) confirmed from multiple developer sources; CSS isolation pattern is community-standard but no single authoritative spec
- Data source (gspread): HIGH — official gspread docs confirm `service_account_from_dict()` pattern

**Research date:** 2026-03-06
**Valid until:** 2026-09-06 (stable APIs; entry points spec changes rarely)
