# Presentation Framework v0.2.0 — Design Document

**Date:** 2026-03-02
**Approach:** Hybrid Smart Layout Engine + CSS Adaptive Sizing
**Scope:** Layout analysis, new layouts, DX improvements, export, visual polish

---

## 1. Layout Analysis & Build Warnings

### LayoutAnalyzer (`pf/analyzer.py`)

A new build phase between data resolution and template rendering. Estimates rendered height of each slide and warns when content exceeds usable canvas area.

**Usable canvas:** 720px total - 80px padding (top+bottom) - ~65px header = ~575px usable content area.

**Height estimation model:**
- Each block type has a known base height + per-item height stored in a `SIZE_MODEL` dict
- Column height = sum of block heights + inter-block gaps
- Slide height = max(column heights) + header height
- Constants are tunable per-component

**Build output:**
```
Building slides...
  slide 01 (title)
  slide 02 (two-column)
  slide 03 (two-column): left column ~640px of 575px usable (11% over)
     Consider: reduce items in 'card' blocks or split into 2 slides
  slide 04 (data-table)
Built 4 slides -> slides/
```

### CSS Density Hints

The builder calculates a density level per slide and injects it as a CSS custom property:
- `--pf-density: normal` (content fits comfortably)
- `--pf-density: high` (content is tight, near overflow)

CSS uses `clamp()` to adapt sizing:
```css
.card-text { font-size: clamp(11px, var(--pf-body-size), 14px); }
.card { padding: clamp(12px, var(--pf-card-pad), 20px); }
```

When density is high, sizes shrink toward minimums. When normal, defaults apply.

---

## 2. New Layout Types

### `image` layout
- Full-bleed or split image with optional overlay text
- Modes via `position` field:
  - `full` — image fills 1280x720, text overlaid with gradient scrim
  - `split` — image takes one half, text content the other (configurable `side: left|right`)
- Image source: local path or URL (copied to output during build)
- Fields: `image`, `position`, `side`, `title`, `caption`

### `section` layout (divider)
- Bold, minimal slide for separating deck sections
- Large centered section number + title, optional subtitle
- Accent color used prominently (full-width bar or accent background region)
- Auto-numbers based on count of preceding `section` slides

### `quote` layout
- Large centered quotation with decorative quote marks
- Attribution line (author, role, source)
- Optional background image with scrim
- Heading font at ~36px for quote, subheading font for attribution
- Fields: `text`, `author`, `role`, `source`, `background_image`

### `timeline` layout
- 3-6 horizontal connected steps
- Each node: icon, title, description
- Connected by horizontal line with accent-colored dots
- Fields: `title`, `steps[]` each with `icon`, `title`, `description`

---

## 3. Developer Experience

### Live-reload `pf serve`
- Watches `presentation.yaml`, `metrics.json`, and `templates/` for changes
- On change: auto-rebuild + SSE reload signal to browser
- Small JS snippet in navigator listens for SSE, calls `location.reload()`
- New dependency: `watchdog` (pure Python, filesystem events)

### YAML Schema Validation
- Validates `presentation.yaml` against a JSON Schema before building
- Catches: missing required fields, invalid layout names, wrong block types, type mismatches
- Clear errors: `Error in slide 3: block type 'chart' is not valid for 'two-column' layout`
- Schema file: `pf/schema.json` (bundled)

### Better Error Messages
- Template rendering errors include slide number and layout name
- Metrics interpolation failures show the full unresolved path
- Colored terminal output using Click's `style()` (already a dependency)

---

## 4. Export & Sharing

### PDF Export — `pf pdf`
- New CLI command: `pf pdf [-c config] [-m metrics] [-o output.pdf]`
- Uses Playwright (headless Chromium) to render + print each slide
- Each slide = one landscape 16:9 page
- **Optional dependency:** `pip install pf[pdf]` installs Playwright
- Core framework stays lightweight; PDF is opt-in
- Graceful fallback: `pf pdf` without Playwright prints install instructions

### Speaker Notes
- New optional `notes` field on any slide in YAML
- Embedded as `<aside class="notes">` in slide HTML (hidden by default)
- Navigator keyboard shortcut: **N** key opens speaker notes panel
- `pf pdf --notes` includes notes below each slide page

---

## 5. Visual Polish

### Slide Transitions
- CSS-based transitions in navigator between slides
- Default: smooth fade (opacity transition on iframe src swap)
- Per-slide `transition` field: `fade`, `slide-left`, `slide-up`, `none`
- Navigator JS applies CSS class to iframe wrapper, waits for transition end, swaps src
- Pure CSS `transition` + `transform`, no animation library

### Typography Scaling (CSS Adaptive)
- `clamp()` functions driven by `--pf-density` custom property
- Headers: `clamp(32px, var(--pf-header-size), 42px)`
- Body: `clamp(11px, var(--pf-body-size), 14px)`
- Padding/gaps: `clamp(15px, var(--pf-gap), 25px)`
- Dense slides shrink gracefully, sparse slides breathe

### Expanded Theme Options
- New optional YAML fields:
  ```yaml
  theme:
    secondary_accent: "#5B8FA8"  # second accent for charts/highlights
    style: "modern"               # "modern" (default), "minimal", "bold"
  ```
- `style` presets adjust: border radii, shadow depth, accent usage, header weight
- `secondary_accent` for alternating colors in timelines, charts, multi-item highlights

---

## Dependencies

| Dependency | Type | Purpose |
|-----------|------|---------|
| watchdog | Required (new) | Filesystem watching for live-reload |
| playwright | Optional (`pf[pdf]`) | PDF export via headless Chromium |

All existing dependencies (Jinja2, PyYAML, Click) remain unchanged.

---

## Files Changed/Added

| File | Change |
|------|--------|
| `pf/analyzer.py` | NEW — LayoutAnalyzer + SIZE_MODEL |
| `pf/schema.json` | NEW — YAML validation schema |
| `pf/builder.py` | Modified — integrate analyzer, density hints, image copying, notes |
| `pf/cli.py` | Modified — `pf pdf` command, colored output, live-reload serve |
| `pf/pdf.py` | NEW — PDF export with Playwright |
| `templates/layouts/image.html.j2` | NEW |
| `templates/layouts/section.html.j2` | NEW |
| `templates/layouts/quote.html.j2` | NEW |
| `templates/layouts/timeline.html.j2` | NEW |
| `templates/present.html.j2` | Modified — SSE listener, transitions, notes panel |
| `theme/variables.css` | Modified — clamp() values, density properties, secondary accent |
| `theme/base.css` | Modified — density-aware sizing |
| `theme/components.css` | Modified — new layout styles, adaptive sizing |
| `theme/transitions.css` | NEW — slide transition animations |
| `setup.py` | Modified — watchdog dep, optional playwright, version bump |
| `tests/` | Extended — analyzer tests, new layout tests, schema tests |
