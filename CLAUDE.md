# Presentation Framework

YAML + JSON → Jinja2 → HTML slide deck generator. Fixed 1280×720px slides.

## Tech Stack

- **Python 3.10+**: Click (CLI), Jinja2 (templates), PyYAML, jsonschema, watchdog (live-reload)
- **Frontend**: CSS Grid/Flexbox, vanilla JS, optional KaTeX math
- **Optional**: Playwright (PDF/PPTX export), python-pptx (PowerPoint), FastMCP (MCP server)

## CLI Commands

```
pf init <name>       # Scaffold new project (presentation.yaml + metrics.json)
pf build -c X -m Y   # Build slides → output dir
pf serve --watch      # Dev server with live-reload (SSE)
pf pdf                # Export to PDF (requires pip install pf[pdf])
pf pptx               # Export to PowerPoint (requires pip install pf[pptx])
pf zip                # Package slides into .zip
```

## Architecture & Data Flow

1. `presentation.yaml` defines meta, theme, slides (layout + data per slide)
2. `metrics.json` provides data; `{{ metrics.x.y }}` refs are resolved at build time
3. `PresentationBuilder` validates config against `pf/schema.json`, runs layout analyzer, renders Jinja2 templates
4. Output: individual `slide_XX.html` files + `present.html` navigator + `theme/` CSS

## Key Files

| File | Purpose |
|------|---------|
| `pf/cli.py` | Click CLI: init, build, serve, pdf, pptx, zip commands |
| `pf/builder.py` | `PresentationBuilder` — core build pipeline |
| `pf/analyzer.py` | `LayoutAnalyzer` — estimates content height, warns on overflow |
| `pf/contrast.py` | WCAG 2.1 contrast ratio checker (build-time warnings) |
| `pf/schema.json` | JSON Schema for presentation.yaml validation |
| `pf/pdf.py` | Playwright-based PDF export (optional dep) |
| `pf/pptx.py` | Image-based PowerPoint export (optional dep) |
| `pf/mcp_server.py` | FastMCP server — build, validate, contrast, layouts, init tools |
| `templates/` | Jinja2 templates: `base.html.j2`, `present.html.j2`, `layouts/*.html.j2` |
| `theme/` | CSS: `variables.css`, `base.css`, `components.css`, `layouts.css` |

## Layouts (10)

`title` `two-column` `three-column` `data-table` `stat-grid` `closing` `image` `section` `quote` `timeline`

## Theme Config (presentation.yaml)

```yaml
theme:
  primary: "#1C2537"          # Background color
  accent: "#C4A962"           # Highlight color
  secondary_accent: "#5B8FA8" # Optional second accent
  style: modern|minimal|bold  # Style preset
  math: true                  # Enable KaTeX
  fonts:
    heading: "Playfair Display"
    subheading: "Montserrat"
    body: "Lato"
```

## Testing

```
pytest tests/ -v              # All tests
pytest tests/test_builder.py  # Specific module
```

Tests use `pytest` + `tmp_path` fixtures. Test files mirror source modules.

## Conventions

- Builder warnings stored as `_warnings` and `_contrast_warnings` attributes
- Layout templates at `templates/layouts/{name}.html.j2`
- Density analysis: `data-density` attr set per slide (`sparse`/`normal`/`dense`/`very-dense`)
- Metrics interpolation: `{{ metrics.path.to.value }}` resolved before rendering
- Errors: Click exceptions for user-facing errors, structured dicts for MCP tools
