# Presentation Framework

YAML + JSON → Jinja2 → HTML slide deck generator. Fixed 1280×720px slides.

## Agent Role

You help users build branded HTML slide decks. Your primary workflow:
1. Gather the user's content (topic, data, structure preferences)
2. Create `metrics.json` with all dynamic data — never hardcode numbers in YAML
3. Create `presentation.yaml` with slide definitions referencing `{{ metrics.path }}` for data
4. Build with `pf build -c presentation.yaml -m metrics.json -o slides --open`
5. Iterate: review output, fix overflow warnings, adjust layouts

**Key principle:** All data flows from `metrics.json`. Slide YAML references metrics via `{{ metrics.x.y }}` interpolation. This separation lets users update data without touching slide structure.

## Agent Workflow

### Building a New Presentation
1. **Structure the data** — Create `metrics.json` with all numbers, lists, benchmarks, costs
2. **Choose layouts** — Pick from 11 layouts based on content type (see SKILL.md for full data shapes):
   - `title` — Opening slide with hero title and feature icons
   - `two-column` — Main workhorse with typed content blocks (cards, tables, stats, bars, insights)
   - `three-column` — Comparisons and multi-category content
   - `data-table` — Benchmark tables with sections, bars, and insights
   - `stat-grid` — KPI dashboards with stat boxes
   - `chart` — Interactive Plotly charts (bar, line, pie, scatter). Requires `theme.charts: true`
   - `section` — Section dividers between major topics
   - `quote` — Centered quotation with attribution
   - `image` — Full-bleed or split image
   - `timeline` — Horizontal step visualization (2-6 steps)
   - `closing` — Thank you / Q&A with contact pills
3. **Write slides** — Each slide has `layout` + `data` (and optional `notes`, `transition`)
4. **Build and check** — Run `pf build`, review warnings, open `present.html`
5. **Iterate** — Fix overflow warnings by reducing content or splitting slides

### Adding a Slide to an Existing Deck
1. Read the existing `presentation.yaml` to understand the structure
2. Add any new data to `metrics.json`
3. Insert the new slide entry in the `slides` list
4. Build and verify

### Modifying Theme / Branding
1. Edit the `theme` section in `presentation.yaml`
2. Change `primary` (background) and `accent` (highlight) hex colors to match the brand
3. Optionally set `secondary_accent`, `style` preset (modern/minimal/bold), and custom fonts
4. All CSS custom properties are auto-derived from hex colors at build time

## Common Mistakes

1. **Hardcoding data in YAML** — Always put numbers/metrics in `metrics.json`, reference via `{{ metrics.path }}`
2. **Overfilling slides** — Each slide is 1280×720px. Two-column slides with 4+ cards per column will overflow. Split into multiple slides.
3. **Wrong block type for layout** — `two-column` uses `left`/`right` lists. `three-column` and `stat-grid` use `columns`. `data-table` uses `sections`. Check SKILL.md.
4. **Missing `theme.math: true`** — LaTeX `$...$` and `$$...$$` won't render without enabling KaTeX
5. **Missing `theme.charts: true`** — Chart layout needs Plotly enabled in theme config
6. **Wrong icon format in closing layout** — `closing` info_items use full FA classes (`"fa-brands fa-github"`), not just icon names
7. **Forgetting metrics.json** — Build succeeds but `{{ metrics.x }}` appears as literal text

## MCP Server

When available (`.mcp.json` configured), use these tools:
- `build_presentation(config_path, metrics_path, output_dir)` — Build slides, returns warnings
- `validate_config(config_path)` — Validate YAML against schema
- `check_contrast(primary, accent, secondary_accent)` — WCAG contrast check
- `list_layouts()` — List available layouts with descriptions
- `get_layout_example(layout_name)` — Get YAML data shape for a specific layout
- `init_presentation(name, directory)` — Scaffold a new project

## Tech Stack

- **Python 3.10+**: Click (CLI), Jinja2 (templates), PyYAML, jsonschema, watchdog (live-reload)
- **Frontend**: CSS Grid/Flexbox, vanilla JS, optional KaTeX math, optional Plotly charts
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
