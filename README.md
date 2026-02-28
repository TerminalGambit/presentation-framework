# Presentation Framework

A reusable HTML presentation framework that generates branded slide decks from YAML configuration and JSON metrics data. Built with Jinja2 templates, a shared CSS theme, and an iframe-based navigator with keyboard controls.

## Features

- **6 layout templates** — title, two-column, three-column, data-table, stat-grid, closing
- **Metrics interpolation** — `{{ metrics.x.y }}` references in YAML pull live data from JSON
- **Shared CSS theme** — Navy + gold design system with cards, stat boxes, tables, bar charts, pills, and more
- **Navigator** — Keyboard nav (← → arrows), grid overview (G), fullscreen (F), progress bar
- **CLI tooling** — `pf init`, `pf build`, `pf serve`
- **AI-ready** — `SKILL.md` teaches AI agents to build presentations autonomously

## Installation

```bash
pip install -e /path/to/presentation-framework
```

Verify:
```bash
pf --help
```

## Quick Start

```bash
# 1. Scaffold a new project
pf init my-deck

# 2. Edit the config and data files
#    my-deck/presentation.yaml  — slide definitions
#    my-deck/metrics.json       — data for interpolation

# 3. Build
pf build --config my-deck/presentation.yaml \
         --metrics my-deck/metrics.json \
         --output my-deck/slides

# 4. Preview
pf serve --dir my-deck/slides --port 8080
# Open http://localhost:8080/present.html
```

## Commands

| Command | Description |
|---------|-------------|
| `pf init <name>` | Scaffold a new presentation project with starter files |
| `pf build` | Build slides from `presentation.yaml` + `metrics.json` |
| `pf serve` | Start local HTTP server to preview slides |

### `pf build` Options
- `--config / -c` — Path to presentation.yaml (default: `presentation.yaml`)
- `--metrics / -m` — Path to metrics.json (default: `metrics.json`)
- `--output / -o` — Output directory (default: `slides`)

### `pf serve` Options
- `--dir / -d` — Directory to serve (default: `slides`)
- `--port / -p` — Port number (default: `8080`)

## Project Structure

```
my-deck/
├── presentation.yaml   # Slide layouts + content + metrics refs
├── metrics.json        # All dynamic data
└── slides/             # Output (generated)
    ├── slide_01.html
    ├── slide_02.html
    ├── present.html    # Navigator — open this in browser
    └── theme/
        ├── variables.css
        ├── base.css
        └── components.css
```

## Data Pipeline

All dynamic values must come from `metrics.json` — never hardcode data in YAML.

```
metrics.json ──┐
               ├──► pf build ──► slides/
presentation.yaml ─┘
```

Use `{{ metrics.path.to.value }}` in any string inside `presentation.yaml`:

```yaml
# Given metrics.json: {"summary": {"total": 128}}
data:
  title: "{{ metrics.summary.total }} Assets Tracked"
  # Output: "128 Assets Tracked"
```

## Available Layouts

1. **`title`** — Hero/opening slide with decorative frame, large heading, feature grid
2. **`two-column`** — Main content layout with typed content blocks (cards, stats, tables, bars, insights)
3. **`three-column`** — Three-column grid for comparisons
4. **`data-table`** — Benchmark/comparison tables with insights
5. **`stat-grid`** — KPI dashboard with stat boxes and cards
6. **`closing`** — Thank you / Q&A with pills and info items

See `SKILL.md` for complete data shapes and examples for each layout.

## Theme Customization

Edit `presentation.yaml` theme section:

```yaml
theme:
  primary: "#1C2537"       # Background color
  accent: "#C4A962"        # Accent / highlight color
  fonts:
    heading: "Playfair Display"
    subheading: "Montserrat"
    body: "Lato"
```

For deeper CSS changes, edit the files in `theme/`:
- `variables.css` — Design tokens (colors, fonts, spacing)
- `base.css` — Slide container, header, background patterns
- `components.css` — Cards, stat boxes, tables, bars, pills, insights

## Adding Custom Layouts

1. Create `templates/layouts/my-layout.html.j2`
2. Extend `base.html.j2` and define `{% block content %}`
3. Import partials as needed
4. Reference in YAML as `layout: my-layout`

```jinja2
{% extends "base.html.j2" %}
{% from "partials/card.html.j2" import challenge_card %}

{% block content %}
{% include "partials/header.html.j2" %}
<!-- Your layout HTML here -->
{% endblock %}
```

## Example

A complete JEMA presentation is included in `examples/`:

```bash
pf build --config examples/presentation.yaml \
         --metrics examples/metrics.json \
         --output examples/slides

open examples/slides/present.html
```

## Development

```bash
# Install in dev mode
pip install -e .

# Run tests
pytest tests/
```

## Navigator Keyboard Shortcuts

- **← →** — Previous / next slide
- **G** — Grid overview (click to jump)
- **F** — Toggle fullscreen
- **Esc** — Exit grid / fullscreen
