# Presentation Framework

A reusable HTML presentation framework that generates branded slide decks from YAML configuration and JSON metrics data. Built with Jinja2 templates, a shared CSS theme, and an iframe-based navigator with keyboard controls.

## Features

- **10 layout templates** — title, two-column, three-column, data-table, stat-grid, closing, image, section, quote, timeline
- **Metrics interpolation** — `{{ metrics.x.y }}` references in YAML pull live data from JSON
- **Shared CSS theme** — Customizable design system with secondary accent and style presets (modern/minimal/bold)
- **Navigator** — Keyboard nav, grid overview (G), fullscreen (F), speaker notes (N), progress bar
- **Live-reload** — `pf serve --watch` auto-rebuilds and refreshes the browser on file changes
- **CSS transitions** — Slide transitions (fade, slide, zoom, flip) with per-slide configuration
- **Layout warnings** — Build-time overflow detection with density-aware CSS adaptive sizing
- **YAML validation** — Schema validation with clear, actionable error messages
- **PDF export** — Optional Playwright-based PDF export via `pf pdf`
- **CLI tooling** — `pf init`, `pf build`, `pf serve`, `pf zip`, `pf pdf`
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
| `pf serve` | Start local HTTP server with live-reload |
| `pf zip` | Package built slides into a shareable `.zip` |
| `pf pdf` | Export slides to PDF (requires Playwright) |

### `pf build` Options
- `--config / -c` — Path to presentation.yaml (default: `presentation.yaml`)
- `--metrics / -m` — Path to metrics.json (default: `metrics.json`)
- `--output / -o` — Output directory (default: `slides`)
- `--open` — Open in browser after build

### `pf serve` Options
- `--dir / -d` — Directory to serve (default: `slides`)
- `--port / -p` — Port number (default: `8080`)
- `--watch / --no-watch` — Watch for changes and auto-rebuild (default: on)
- `--config / -c` — Config file for rebuild (default: `presentation.yaml`)
- `--metrics / -m` — Metrics file for rebuild (default: `metrics.json`)

### `pf pdf` Options
- `--config / -c` — Path to presentation.yaml (default: `presentation.yaml`)
- `--metrics / -m` — Path to metrics.json (default: `metrics.json`)
- `--output / -o` — Output PDF path (default: `presentation.pdf`)
- `--notes` — Include speaker notes

Requires: `pip install presentation-framework[pdf]` and `playwright install chromium`

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
7. **`image`** — Full-bleed or split image with optional title and caption
8. **`section`** — Section divider with large title, subtitle, and optional number
9. **`quote`** — Centered quote with decorative marks and attribution
10. **`timeline`** — Horizontal step visualization with icons and descriptions

See `SKILL.md` for complete data shapes and examples for each layout.

## Theme Options

### Style Presets
```yaml
theme:
  style_preset: modern  # modern (default), minimal, or bold
```

### Secondary Accent
```yaml
theme:
  accent: "#C4A962"
  secondary_accent: "#4A90D9"  # Optional second accent color
```

### Speaker Notes
Add notes to any slide:
```yaml
slides:
  - layout: title
    notes: "Remember to introduce the team before this slide."
    data:
      title: "My Title"
```
Press **N** during presentation to toggle the notes panel.

### Slide Transitions
```yaml
theme:
  transition: fade         # Default transition for all slides (fade/slide/zoom/flip)
  transition_speed: 0.5s   # Duration

slides:
  - layout: title
    transition: zoom       # Override per-slide
    data: ...
```

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
- **N** — Toggle speaker notes
- **H** — Toggle UI (hide controls)
- **Esc** — Exit grid / fullscreen
- **1-9, 0** — Jump to slide 1-10
