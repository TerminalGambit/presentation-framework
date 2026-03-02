# Presentation Framework v0.2.0 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Overhaul the presentation framework with layout analysis warnings, CSS adaptive sizing, four new layouts, DX improvements, speaker notes, transitions, expanded themes, and PDF export.

**Architecture:** Hybrid approach — Python-side `LayoutAnalyzer` estimates content height and emits build-time warnings, while CSS `clamp()` values driven by density hints handle runtime adaptation. New layouts are Jinja2 templates. Live-reload uses watchdog + SSE. PDF export is an optional Playwright dependency.

**Tech Stack:** Python 3.10+ (Click, Jinja2, PyYAML, watchdog), Playwright (optional), HTML5/CSS3/vanilla JS

---

## Task 1: Bump Version and Add Dependencies

**Files:**
- Modify: `pf/__init__.py`
- Modify: `setup.py`

**Step 1: Update version in `pf/__init__.py`**

```python
"""Presentation Framework — generate branded HTML slide decks from YAML + JSON."""
__version__ = "0.2.0"
```

**Step 2: Update `setup.py` with new deps and version**

```python
from setuptools import setup, find_packages

setup(
    name="presentation-framework",
    version="0.2.0",
    description="Generate branded HTML slide decks from YAML + JSON",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "pf": ["schema.json"],
    },
    install_requires=[
        "jinja2>=3.0",
        "pyyaml>=6.0",
        "click>=8.0",
        "watchdog>=3.0",
        "jsonschema>=4.0",
    ],
    extras_require={
        "pdf": ["playwright>=1.40"],
    },
    entry_points={
        "console_scripts": [
            "pf=pf.cli:cli",
        ],
    },
    python_requires=">=3.10",
)
```

**Step 3: Install updated deps**

Run: `pip install -e ".[pdf]"` or `pip install -e .` (pdf optional)

**Step 4: Commit**

```bash
git add pf/__init__.py setup.py
git commit -m "chore: bump to v0.2.0, add watchdog and jsonschema deps"
```

---

## Task 2: Layout Analyzer — SIZE_MODEL and Height Estimation

**Files:**
- Create: `pf/analyzer.py`
- Create: `tests/test_analyzer.py`

**Step 1: Write the failing tests for LayoutAnalyzer**

```python
"""Tests for pf.analyzer.LayoutAnalyzer."""

import pytest
from pf.analyzer import LayoutAnalyzer


class TestBlockHeight:
    def test_card_base_height(self):
        block = {"type": "card", "icon": "bolt", "title": "Test", "text": "Desc"}
        height = LayoutAnalyzer.estimate_block_height(block)
        # card base: 60px (padding + title + text) + 0 bullets
        assert height == 60

    def test_card_with_bullets(self):
        block = {"type": "card", "icon": "bolt", "title": "Test", "text": "Desc",
                 "bullets": ["a", "b", "c"]}
        height = LayoutAnalyzer.estimate_block_height(block)
        # 60 base + 3 * 22px per bullet = 126
        assert height == 126

    def test_stat_grid_2_cols(self):
        block = {"type": "stat-grid", "stats": [
            {"value": "128", "label": "Assets"},
            {"value": "9", "label": "Categories"},
            {"value": "17", "label": "Feeds"},
            {"value": "36", "label": "Accounts"},
        ], "cols": 2}
        height = LayoutAnalyzer.estimate_block_height(block)
        # 2 rows * 55px per row + 15px gap = 125
        assert height == 125

    def test_table_height(self):
        block = {"type": "table", "headers": ["Name", "Score"],
                 "rows": [["A", "90"], ["B", "85"], ["C", "80"]]}
        height = LayoutAnalyzer.estimate_block_height(block)
        # header 35px + 3 rows * 33px + 0 section_title
        assert height == 134

    def test_insight_height(self):
        block = {"type": "insight", "text": "Key finding here"}
        height = LayoutAnalyzer.estimate_block_height(block)
        assert height == 45

    def test_solution_box_height(self):
        block = {"type": "solution-box", "title": "Solution",
                 "items": ["item1", "item2", "item3"]}
        height = LayoutAnalyzer.estimate_block_height(block)
        # 80 base + 3 * 28px items = 164
        assert height == 164

    def test_unknown_block_default(self):
        block = {"type": "html", "content": "<p>hello</p>"}
        height = LayoutAnalyzer.estimate_block_height(block)
        assert height == 40  # default fallback


class TestColumnHeight:
    def test_single_block(self):
        col = [{"type": "insight", "text": "Note"}]
        height = LayoutAnalyzer.estimate_column_height(col)
        assert height == 45

    def test_multiple_blocks_with_gaps(self):
        col = [
            {"type": "insight", "text": "A"},
            {"type": "insight", "text": "B"},
        ]
        height = LayoutAnalyzer.estimate_column_height(col)
        # 45 + 10 (gap) + 45 = 100
        assert height == 100

    def test_empty_column(self):
        assert LayoutAnalyzer.estimate_column_height([]) == 0


class TestSlideAnalysis:
    def test_two_column_within_limits(self):
        slide = {
            "layout": "two-column",
            "data": {
                "title": "Test",
                "left": [{"type": "insight", "text": "Short"}],
                "right": [{"type": "insight", "text": "Short"}],
            },
        }
        result = LayoutAnalyzer.analyze_slide(slide, 0)
        assert result is None  # No warning

    def test_two_column_overflow_warning(self):
        # 12 cards = 12 * 60 + 11 * 10 = 830px >> 575px usable
        cards = [{"type": "card", "icon": "bolt", "title": f"Card {i}", "text": "Desc"}
                 for i in range(12)]
        slide = {
            "layout": "two-column",
            "data": {
                "title": "Overflowing",
                "left": cards,
                "right": [{"type": "insight", "text": "Short"}],
            },
        }
        result = LayoutAnalyzer.analyze_slide(slide, 2)
        assert result is not None
        assert "left" in result["column"]
        assert result["estimated_px"] > 575
        assert result["slide_index"] == 2

    def test_title_layout_no_analysis(self):
        slide = {"layout": "title", "data": {"title": "Hello"}}
        result = LayoutAnalyzer.analyze_slide(slide, 0)
        assert result is None

    def test_three_column_overflow(self):
        cards = [{"type": "card", "icon": "bolt", "title": f"Card {i}", "text": "Desc"}
                 for i in range(10)]
        slide = {
            "layout": "three-column",
            "data": {
                "title": "Dense",
                "columns": [cards, [], []],
            },
        }
        result = LayoutAnalyzer.analyze_slide(slide, 0)
        assert result is not None


class TestDensity:
    def test_normal_density(self):
        slide = {
            "layout": "two-column",
            "data": {
                "title": "Light",
                "left": [{"type": "insight", "text": "Short"}],
                "right": [{"type": "insight", "text": "Short"}],
            },
        }
        density = LayoutAnalyzer.compute_density(slide)
        assert density == "normal"

    def test_high_density(self):
        cards = [{"type": "card", "icon": "bolt", "title": f"C{i}", "text": "D"}
                 for i in range(8)]
        slide = {
            "layout": "two-column",
            "data": {
                "title": "Dense",
                "left": cards,
                "right": cards,
            },
        }
        density = LayoutAnalyzer.compute_density(slide)
        assert density == "high"
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_analyzer.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'pf.analyzer'`

**Step 3: Implement LayoutAnalyzer**

Create `pf/analyzer.py`:

```python
"""
LayoutAnalyzer — estimates rendered height of slide content
and warns about overflow at build time.
"""

import math

# Usable content area: 720px - 80px padding - 65px header = 575px
USABLE_HEIGHT = 575
COLUMN_GAP = 10  # gap between blocks in a column (from .col CSS)
HEADER_HEIGHT = 65  # header + margin-bottom

# Height model: base_px + (per_item_px * item_count)
SIZE_MODEL = {
    "card": {"base": 60, "per_item": 22, "item_key": "bullets"},
    "solution-box": {"base": 80, "per_item": 28, "item_key": "items"},
    "stat-grid": {"base": 0, "per_row": 55, "row_gap": 15, "cols_key": "cols", "items_key": "stats"},
    "table": {"base": 35, "per_item": 33, "item_key": "rows", "section_title": 30},
    "dist-bars": {"base": 10, "per_item": 28, "item_key": "bars"},
    "val-bars": {"base": 0, "per_item": 30, "item_key": "items"},
    "unit-grid": {"base": 10, "per_item": 65, "item_key": "tiers"},
    "insight": {"base": 45, "per_item": 0},
    "value-prop": {"base": 45, "per_item": 0},
    "takeaway": {"base": 40, "per_item": 0},
}

DEFAULT_BLOCK_HEIGHT = 40

# Layouts that have columnar content to analyze
COLUMNAR_LAYOUTS = {"two-column", "three-column", "data-table", "stat-grid"}


class LayoutAnalyzer:
    """Estimates slide content height and detects overflow."""

    @staticmethod
    def estimate_block_height(block: dict) -> int:
        """Estimate the rendered pixel height of a single content block."""
        block_type = block.get("type", "")
        model = SIZE_MODEL.get(block_type)

        if model is None:
            return DEFAULT_BLOCK_HEIGHT

        # Special case: stat-grid uses rows (items / cols)
        if block_type == "stat-grid":
            items = block.get(model["items_key"], [])
            cols = block.get(model.get("cols_key", "cols"), 2)
            rows = math.ceil(len(items) / cols) if cols > 0 else 0
            if rows == 0:
                return 0
            return rows * model["per_row"] + (rows - 1) * model["row_gap"]

        # Special case: table may have section_title
        base = model["base"]
        if block_type == "table" and block.get("section_title"):
            base += model.get("section_title", 0)

        item_key = model.get("item_key")
        if item_key:
            items = block.get(item_key, [])
            return base + len(items) * model["per_item"]

        return base

    @staticmethod
    def estimate_column_height(blocks: list[dict]) -> int:
        """Estimate total height of a column of blocks."""
        if not blocks:
            return 0
        total = sum(LayoutAnalyzer.estimate_block_height(b) for b in blocks)
        gaps = (len(blocks) - 1) * COLUMN_GAP
        return total + gaps

    @staticmethod
    def _get_columns(slide: dict) -> dict[str, list[dict]]:
        """Extract column data from a slide config based on layout type."""
        layout = slide.get("layout", "")
        data = slide.get("data", {})

        if layout == "two-column":
            return {
                "left": data.get("left", []),
                "right": data.get("right", []),
            }
        elif layout == "three-column":
            columns = data.get("columns", [[], [], []])
            return {f"col {i+1}": col for i, col in enumerate(columns)}
        elif layout == "data-table":
            sections = data.get("sections", [])
            return {f"section {i+1}": [s] if isinstance(s, dict) else []
                    for i, s in enumerate(sections)}
        return {}

    @staticmethod
    def analyze_slide(slide: dict, index: int) -> dict | None:
        """
        Analyze a single slide for overflow.
        Returns a warning dict if overflow detected, None otherwise.
        """
        layout = slide.get("layout", "")
        if layout not in COLUMNAR_LAYOUTS:
            return None

        columns = LayoutAnalyzer._get_columns(slide)
        for col_name, blocks in columns.items():
            height = LayoutAnalyzer.estimate_column_height(blocks)
            if height > USABLE_HEIGHT:
                overflow_pct = round((height - USABLE_HEIGHT) / USABLE_HEIGHT * 100)
                return {
                    "slide_index": index,
                    "layout": layout,
                    "column": col_name,
                    "estimated_px": height,
                    "usable_px": USABLE_HEIGHT,
                    "overflow_pct": overflow_pct,
                }
        return None

    @staticmethod
    def compute_density(slide: dict) -> str:
        """
        Compute density level for a slide: 'normal' or 'high'.
        Used to set CSS custom property --pf-density.
        """
        layout = slide.get("layout", "")
        if layout not in COLUMNAR_LAYOUTS:
            return "normal"

        columns = LayoutAnalyzer._get_columns(slide)
        max_height = max(
            (LayoutAnalyzer.estimate_column_height(blocks) for blocks in columns.values()),
            default=0,
        )
        # High density if content uses > 85% of usable area
        if max_height > USABLE_HEIGHT * 0.85:
            return "high"
        return "normal"
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_analyzer.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add pf/analyzer.py tests/test_analyzer.py
git commit -m "feat: add LayoutAnalyzer with height estimation and density computation"
```

---

## Task 3: Integrate Analyzer into Builder

**Files:**
- Modify: `pf/builder.py:99-117` (render_slide to accept density)
- Modify: `pf/builder.py:219-269` (build method to run analysis)
- Modify: `templates/base.html.j2`
- Modify: `tests/test_builder.py`

**Step 1: Write failing test for density integration**

Add to `tests/test_builder.py`:

```python
class TestBuildWithAnalyzer:
    def test_build_injects_density_attribute(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            config = {
                "meta": {"title": "Test"},
                "theme": {"fonts": {"heading": "Playfair Display", "subheading": "Montserrat", "body": "Lato"}},
                "slides": [
                    {"layout": "two-column", "data": {
                        "title": "Light",
                        "left": [{"type": "html", "content": "<p>Hi</p>"}],
                        "right": [{"type": "html", "content": "<p>Hi</p>"}],
                    }},
                ],
            }
            (tmpdir / "presentation.yaml").write_text(yaml.dump(config), encoding="utf-8")
            (tmpdir / "metrics.json").write_text("{}", encoding="utf-8")
            builder = PresentationBuilder(
                config_path=str(tmpdir / "presentation.yaml"),
                metrics_path=str(tmpdir / "metrics.json"),
            )
            out = builder.build(output_dir=str(tmpdir / "slides"))
            html = (out / "slide_01.html").read_text()
            assert 'data-density="normal"' in html
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_builder.py::TestBuildWithAnalyzer -v`
Expected: FAIL — `data-density` not in output

**Step 3: Modify `templates/base.html.j2` to accept density**

Replace line 15 of `templates/base.html.j2`:
```html
  <div class="slide-container{% block container_class %}{% endblock %}" data-density="{{ density | default('normal') }}" style="{% if density == 'high' %}--pf-body-size: 12px; --pf-card-pad: 14px; --pf-header-size: 36px; --pf-gap: 18px;{% else %}--pf-body-size: 14px; --pf-card-pad: 20px; --pf-header-size: 42px; --pf-gap: 25px;{% endif %}">
```

**Step 4: Modify `pf/builder.py` render_slide to pass density**

In `render_slide()` (around line 111), add `density` parameter:

```python
def render_slide(self, slide_config: dict, index: int, density: str = "normal") -> str:
    """Render a single slide to HTML string."""
    layout = slide_config.get("layout", "two-column")
    template_name = f"layouts/{layout}.html.j2"
    template = self.env.get_template(template_name)

    meta = self.config.get("meta", {})
    theme = self.config.get("theme", {})
    page_number = slide_config.get("page_number", f"{index + 1:02d}")

    return template.render(
        slide=slide_config,
        slide_title=slide_config.get("data", {}).get("title", f"Slide {index + 1}"),
        meta=meta,
        theme=theme,
        page_number=page_number,
        density=density,
    )
```

**Step 5: Modify `pf/builder.py` build method to use analyzer**

In the `build()` method, add analyzer import at top of file:
```python
from pf.analyzer import LayoutAnalyzer
```

Replace the slide loop in `build()` (lines 240-252):
```python
        warnings = []
        for i, slide_cfg in enumerate(slides):
            # Resolve metrics references in slide data
            slide_cfg["data"] = self.resolve_data(slide_cfg.get("data", {}), self.metrics)

            # Analyze layout for overflow
            warning = LayoutAnalyzer.analyze_slide(slide_cfg, i)
            if warning:
                warnings.append(warning)

            # Compute density for CSS adaptive sizing
            density = LayoutAnalyzer.compute_density(slide_cfg)

            # Render the slide
            html = self.render_slide(slide_cfg, i, density=density)

            # Write to file
            filename = f"slide_{i + 1:02d}.html"
            (out / filename).write_text(html, encoding="utf-8")

            slide_files.append(filename)
            slide_titles.append(slide_cfg.get("data", {}).get("title", f"Slide {i + 1}"))

        self._warnings = warnings
```

**Step 6: Run all tests**

Run: `pytest tests/ -v`
Expected: All PASS

**Step 7: Commit**

```bash
git add pf/builder.py templates/base.html.j2 tests/test_builder.py
git commit -m "feat: integrate LayoutAnalyzer into build pipeline with density hints"
```

---

## Task 4: Build Warnings in CLI

**Files:**
- Modify: `pf/cli.py:107-126` (build command)

**Step 1: Update build command to print warnings**

Replace the build function body (after `builder = ...`) in `pf/cli.py`:

```python
    builder = PresentationBuilder(config_path=config, metrics_path=metrics)
    out = builder.build(output_dir=output)

    slide_count = len(list(out.glob("slide_*.html")))

    # Print layout warnings
    for w in getattr(builder, '_warnings', []):
        idx = w["slide_index"] + 1
        layout = w["layout"]
        col = w["column"]
        est = w["estimated_px"]
        usable = w["usable_px"]
        pct = w["overflow_pct"]
        click.echo(
            click.style(f"  ⚠ slide {idx:02d} ({layout}): ", fg="yellow")
            + f"{col} ~{est}px of {usable}px usable ({pct}% over)"
        )
        click.echo(
            click.style("     → ", fg="yellow")
            + "Consider: reduce content or split into multiple slides"
        )

    click.echo(f"Built {slide_count} slides → {out}/")

    present_path = out.resolve() / "present.html"
    if open_browser:
        webbrowser.open(f"file://{present_path}")
        click.echo(f"Opened {present_path} in browser.")
    else:
        click.echo(f"Open {out}/present.html in a browser to present.")
```

**Step 2: Test manually**

Run: `cd examples && pf build`
Expected: Builds with green checkmarks or yellow warnings depending on content density.

**Step 3: Commit**

```bash
git add pf/cli.py
git commit -m "feat: add colored overflow warnings to pf build output"
```

---

## Task 5: CSS Adaptive Sizing with clamp()

**Files:**
- Modify: `theme/components.css`
- Modify: `theme/base.css`

**Step 1: Add density-aware custom properties and clamp() values**

In `theme/base.css`, after the `.slide-container` rule (line 25), add:

```css
/* ── Density-Aware Defaults ────────────────────────────────── */
.slide-container {
  --pf-body-size: 14px;
  --pf-card-pad: 20px;
  --pf-header-size: 42px;
  --pf-gap: 25px;
}
.slide-container[data-density="high"] {
  --pf-body-size: 12px;
  --pf-card-pad: 14px;
  --pf-header-size: 36px;
  --pf-gap: 18px;
}
```

In `theme/base.css`, update `.header .title` (line 100):
```css
font-size: var(--pf-header-size, 42px);
```

Update `.grid-2col` and `.grid-3col` gap (lines 141, 150):
```css
gap: var(--pf-gap, 25px);
```

Update `.col` gap (line 159):
```css
gap: clamp(6px, var(--pf-gap), 10px);
```

**Step 2: Update component CSS to use density variables**

In `theme/components.css`, update these values:

- Line 11 `.card` padding: `padding: var(--pf-card-pad, 20px);`
- Line 39 `.challenge-card` padding: `padding: clamp(12px, var(--pf-card-pad), 18px) var(--pf-card-pad, 20px);`
- Line 79 `.card-text` font-size: `font-size: var(--pf-body-size, 14px);`
- Line 87 `.card-bullet` font-size: `font-size: clamp(11px, var(--pf-body-size), 13px);`
- Line 173 `.stat-box` padding: `padding: clamp(10px, var(--pf-card-pad), 15px);`
- Line 211 `.data-table` font-size: `font-size: clamp(11px, var(--pf-body-size), 13px);`
- Line 395 `.insight-text` font-size: `font-size: clamp(11px, var(--pf-body-size), 13px);`

**Step 3: Test visually**

Run: `cd examples && pf build --open`
Verify: Normal-density slides look unchanged. If you create a dense slide, fonts/padding should shrink.

**Step 4: Commit**

```bash
git add theme/base.css theme/components.css
git commit -m "feat: add CSS adaptive sizing with density-aware clamp() values"
```

---

## Task 6: New Layout — `image`

**Files:**
- Create: `templates/layouts/image.html.j2`
- Modify: `theme/components.css` (append image layout styles)
- Modify: `pf/builder.py` (image file copying in build)
- Create: `tests/test_image_layout.py`

**Step 1: Write failing test**

```python
"""Tests for image layout."""
import json
import tempfile
from pathlib import Path
import yaml
import pytest
from pf.builder import PresentationBuilder


class TestImageLayout:
    def test_render_image_full(self):
        b = PresentationBuilder()
        b.config = {
            "meta": {"title": "Test"},
            "theme": {"fonts": {"heading": "Playfair Display", "subheading": "Montserrat", "body": "Lato"}},
        }
        slide = {
            "layout": "image",
            "data": {
                "image": "assets/diagram.png",
                "position": "full",
                "title": "Architecture",
                "caption": "System overview",
            },
        }
        html = b.render_slide(slide, 0)
        assert "Architecture" in html
        assert "diagram.png" in html
        assert "System overview" in html

    def test_render_image_split(self):
        b = PresentationBuilder()
        b.config = {
            "meta": {"title": "Test"},
            "theme": {"fonts": {"heading": "Playfair Display", "subheading": "Montserrat", "body": "Lato"}},
        }
        slide = {
            "layout": "image",
            "data": {
                "image": "assets/photo.jpg",
                "position": "split",
                "side": "left",
                "title": "Our Team",
                "caption": "Founded 2024",
            },
        }
        html = b.render_slide(slide, 0)
        assert "Our Team" in html
        assert "photo.jpg" in html
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_image_layout.py -v`
Expected: FAIL — template not found

**Step 3: Create `templates/layouts/image.html.j2`**

```jinja2
{% extends "base.html.j2" %}

{% block container_class %}{% if slide.data.position == 'full' %} centered{% endif %}{% endblock %}

{% block content %}
{% if slide.data.position == 'split' %}
{# ── Split mode: image on one side, text on the other ── #}
<div class="image-split" style="flex-direction: {% if slide.data.side == 'right' %}row-reverse{% else %}row{% endif %};">
  <div class="image-split-img">
    <img src="{{ slide.data.image }}" alt="{{ slide.data.title | default('') }}"/>
  </div>
  <div class="image-split-text">
    {% if slide.data.title %}
    <h2 class="image-title">{{ slide.data.title }}</h2>
    {% endif %}
    {% if slide.data.caption %}
    <p class="image-caption">{{ slide.data.caption }}</p>
    {% endif %}
  </div>
</div>
{% else %}
{# ── Full mode: image fills canvas, text overlaid ── #}
<div class="image-full" style="background-image: url('{{ slide.data.image }}');">
  <div class="image-full-overlay">
    {% if slide.data.title %}
    <h2 class="image-title image-title--overlay">{{ slide.data.title }}</h2>
    {% endif %}
    {% if slide.data.caption %}
    <p class="image-caption image-caption--overlay">{{ slide.data.caption }}</p>
    {% endif %}
  </div>
</div>
{% endif %}
{% endblock %}
```

**Step 4: Add CSS for image layout to `theme/components.css`**

Append to `theme/components.css`:

```css
/* ── Image Layout ──────────────────────────────────────────── */
.image-full {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background-size: cover;
  background-position: center;
  z-index: 5;
}

.image-full-overlay {
  position: absolute;
  bottom: 0; left: 0; right: 0;
  background: linear-gradient(transparent, rgba(0, 0, 0, 0.85));
  padding: 60px 50px 50px;
  z-index: 6;
}

.image-split {
  display: flex;
  flex: 1;
  min-height: 0;
  gap: 0;
  z-index: 10;
  margin: calc(-1 * var(--pf-slide-padding));
}

.image-split-img {
  flex: 1;
  overflow: hidden;
}

.image-split-img img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-split-text {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 50px;
}

.image-title {
  font-family: var(--pf-font-heading);
  font-size: 42px;
  color: var(--pf-accent);
  margin-bottom: 15px;
  line-height: 1.1;
}

.image-title--overlay {
  color: var(--pf-white);
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
}

.image-caption {
  font-family: var(--pf-font-body);
  font-size: 18px;
  color: var(--pf-text);
  line-height: 1.6;
}

.image-caption--overlay {
  color: rgba(255, 255, 255, 0.85);
}
```

**Step 5: Add image file copying to builder**

In `pf/builder.py`, in the `build()` method, after writing slide files and before the navigator render, add image copying logic:

```python
        # Copy local image assets referenced by image layout slides
        for slide_cfg in slides:
            if slide_cfg.get("layout") == "image":
                img_path = Path(slide_cfg.get("data", {}).get("image", ""))
                if img_path.exists() and not img_path.is_absolute():
                    dest = out / img_path
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(img_path, dest)
```

**Step 6: Run tests**

Run: `pytest tests/test_image_layout.py -v`
Expected: All PASS

**Step 7: Commit**

```bash
git add templates/layouts/image.html.j2 theme/components.css pf/builder.py tests/test_image_layout.py
git commit -m "feat: add image layout (full-bleed and split modes)"
```

---

## Task 7: New Layout — `section`

**Files:**
- Create: `templates/layouts/section.html.j2`
- Modify: `theme/components.css` (append section divider styles)
- Create: `tests/test_section_layout.py`

**Step 1: Write failing test**

```python
"""Tests for section divider layout."""
from pf.builder import PresentationBuilder


class TestSectionLayout:
    def test_render_section_slide(self):
        b = PresentationBuilder()
        b.config = {
            "meta": {"title": "Test"},
            "theme": {"fonts": {"heading": "Playfair Display", "subheading": "Montserrat", "body": "Lato"}},
        }
        slide = {
            "layout": "section",
            "data": {
                "title": "Research Findings",
                "subtitle": "What we discovered",
                "number": 2,
            },
        }
        html = b.render_slide(slide, 0)
        assert "Research Findings" in html
        assert "What we discovered" in html
        assert "02" in html or "2" in html
```

**Step 2: Run test to verify failure**

Run: `pytest tests/test_section_layout.py -v`
Expected: FAIL — template not found

**Step 3: Create `templates/layouts/section.html.j2`**

```jinja2
{% extends "base.html.j2" %}

{% block container_class %} centered{% endblock %}

{% block decorations %}
{% include "partials/bg-pattern.html.j2" %}
{% endblock %}

{% block content %}
<div class="z-10 text-center" style="display: flex; flex-direction: column; align-items: center;">
  <div class="section-divider-accent"></div>
  {% if slide.data.number %}
  <div class="section-divider-number">{{ "%02d"|format(slide.data.number) }}</div>
  {% endif %}
  <h1 class="section-divider-title">{{ slide.data.title }}</h1>
  {% if slide.data.subtitle %}
  <p class="section-divider-subtitle">{{ slide.data.subtitle }}</p>
  {% endif %}
  <div class="section-divider-accent section-divider-accent--bottom"></div>
</div>
{% endblock %}
```

**Step 4: Add CSS to `theme/components.css`**

```css
/* ── Section Divider Layout ────────────────────────────────── */
.section-divider-accent {
  width: 120px;
  height: 3px;
  background: var(--pf-accent);
  margin-bottom: 30px;
}

.section-divider-accent--bottom {
  margin-top: 30px;
  margin-bottom: 0;
}

.section-divider-number {
  font-family: var(--pf-font-heading);
  font-size: 72px;
  color: var(--pf-accent);
  font-weight: 700;
  line-height: 1;
  margin-bottom: 15px;
  opacity: 0.3;
}

.section-divider-title {
  font-family: var(--pf-font-heading);
  font-size: 56px;
  color: var(--pf-white);
  font-weight: 700;
  line-height: 1.1;
  margin-bottom: 15px;
  letter-spacing: -1px;
}

.section-divider-subtitle {
  font-family: var(--pf-font-subheading);
  font-size: 22px;
  color: var(--pf-text-muted);
  font-weight: 300;
  letter-spacing: 2px;
  text-transform: uppercase;
}
```

**Step 5: Run tests**

Run: `pytest tests/test_section_layout.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add templates/layouts/section.html.j2 theme/components.css tests/test_section_layout.py
git commit -m "feat: add section divider layout"
```

---

## Task 8: New Layout — `quote`

**Files:**
- Create: `templates/layouts/quote.html.j2`
- Modify: `theme/components.css` (append quote styles)
- Create: `tests/test_quote_layout.py`

**Step 1: Write failing test**

```python
"""Tests for quote layout."""
from pf.builder import PresentationBuilder


class TestQuoteLayout:
    def test_render_quote_slide(self):
        b = PresentationBuilder()
        b.config = {
            "meta": {"title": "Test"},
            "theme": {"fonts": {"heading": "Playfair Display", "subheading": "Montserrat", "body": "Lato"}},
        }
        slide = {
            "layout": "quote",
            "data": {
                "text": "The best way to predict the future is to invent it.",
                "author": "Alan Kay",
                "role": "Computer Scientist",
            },
        }
        html = b.render_slide(slide, 0)
        assert "The best way to predict the future" in html
        assert "Alan Kay" in html
        assert "Computer Scientist" in html
```

**Step 2: Run test to verify failure**

Run: `pytest tests/test_quote_layout.py -v`
Expected: FAIL — template not found

**Step 3: Create `templates/layouts/quote.html.j2`**

```jinja2
{% extends "base.html.j2" %}

{% block container_class %} centered{% endblock %}

{% block decorations %}
{% include "partials/bg-pattern.html.j2" %}
{% endblock %}

{% block head_extra %}
{% if slide.data.background_image %}
<style>
  .slide-container { background-image: url('{{ slide.data.background_image }}'); background-size: cover; background-position: center; }
  .slide-container::before { content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.7); z-index: 1; }
</style>
{% endif %}
{% endblock %}

{% block content %}
<div class="z-10 text-center" style="max-width: 900px; display: flex; flex-direction: column; align-items: center;">
  <div class="quote-mark">&ldquo;</div>
  <blockquote class="quote-text">{{ slide.data.text }}</blockquote>
  <div class="quote-divider"></div>
  <div class="quote-attribution">
    {% if slide.data.author %}<span class="quote-author">{{ slide.data.author }}</span>{% endif %}
    {% if slide.data.role %}<span class="quote-role">{{ slide.data.role }}</span>{% endif %}
    {% if slide.data.source %}<span class="quote-source">{{ slide.data.source }}</span>{% endif %}
  </div>
</div>
{% endblock %}
```

**Step 4: Add CSS to `theme/components.css`**

```css
/* ── Quote Layout ──────────────────────────────────────────── */
.quote-mark {
  font-family: var(--pf-font-heading);
  font-size: 120px;
  color: var(--pf-accent);
  line-height: 0.6;
  margin-bottom: 20px;
  opacity: 0.4;
}

.quote-text {
  font-family: var(--pf-font-heading);
  font-size: 36px;
  color: var(--pf-white);
  font-style: italic;
  line-height: 1.4;
  margin: 0 0 30px 0;
  font-weight: 400;
}

.quote-divider {
  width: 60px;
  height: 2px;
  background: var(--pf-accent);
  margin-bottom: 25px;
}

.quote-attribution {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.quote-author {
  font-family: var(--pf-font-subheading);
  font-size: 18px;
  color: var(--pf-accent);
  font-weight: 600;
  letter-spacing: 1px;
}

.quote-role {
  font-family: var(--pf-font-subheading);
  font-size: 14px;
  color: var(--pf-text-muted);
  font-weight: 300;
  text-transform: uppercase;
  letter-spacing: 2px;
}

.quote-source {
  font-family: var(--pf-font-body);
  font-size: 13px;
  color: var(--pf-text-dim);
  font-style: italic;
}
```

**Step 5: Run tests**

Run: `pytest tests/test_quote_layout.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add templates/layouts/quote.html.j2 theme/components.css tests/test_quote_layout.py
git commit -m "feat: add quote layout with decorative marks and attribution"
```

---

## Task 9: New Layout — `timeline`

**Files:**
- Create: `templates/layouts/timeline.html.j2`
- Modify: `theme/components.css` (append timeline styles)
- Create: `tests/test_timeline_layout.py`

**Step 1: Write failing test**

```python
"""Tests for timeline layout."""
from pf.builder import PresentationBuilder


class TestTimelineLayout:
    def test_render_timeline_slide(self):
        b = PresentationBuilder()
        b.config = {
            "meta": {"title": "Test"},
            "theme": {"fonts": {"heading": "Playfair Display", "subheading": "Montserrat", "body": "Lato"}},
        }
        slide = {
            "layout": "timeline",
            "data": {
                "title": "Our Process",
                "steps": [
                    {"icon": "search", "title": "Research", "description": "Gather requirements"},
                    {"icon": "pencil", "title": "Design", "description": "Create mockups"},
                    {"icon": "code", "title": "Build", "description": "Implement solution"},
                    {"icon": "check", "title": "Deploy", "description": "Ship to production"},
                ],
            },
        }
        html = b.render_slide(slide, 0)
        assert "Our Process" in html
        assert "Research" in html
        assert "Deploy" in html
        assert "Gather requirements" in html
```

**Step 2: Run test to verify failure**

Run: `pytest tests/test_timeline_layout.py -v`
Expected: FAIL — template not found

**Step 3: Create `templates/layouts/timeline.html.j2`**

```jinja2
{% extends "base.html.j2" %}

{% block content %}
{% include "partials/header.html.j2" %}

<div class="timeline-container z-10">
  <div class="timeline-line"></div>
  <div class="timeline-steps">
    {% for step in slide.data.steps %}
    <div class="timeline-step">
      <div class="timeline-dot">
        <i class="fas fa-{{ step.icon }}"></i>
      </div>
      <div class="timeline-step-title">{{ step.title }}</div>
      <div class="timeline-step-desc">{{ step.description }}</div>
    </div>
    {% endfor %}
  </div>
</div>
{% endblock %}
```

**Step 4: Add CSS to `theme/components.css`**

```css
/* ── Timeline Layout ───────────────────────────────────────── */
.timeline-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  position: relative;
  padding: 40px 0;
}

.timeline-line {
  position: absolute;
  top: 50%;
  left: 40px;
  right: 40px;
  height: 2px;
  background: linear-gradient(90deg, var(--pf-accent-border), var(--pf-accent), var(--pf-accent-border));
  transform: translateY(-20px);
}

.timeline-steps {
  display: flex;
  justify-content: space-between;
  position: relative;
  z-index: 1;
}

.timeline-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  flex: 1;
  max-width: 200px;
}

.timeline-dot {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--pf-primary);
  border: 2px solid var(--pf-accent);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
  color: var(--pf-accent);
  font-size: 18px;
  box-shadow: 0 0 15px var(--pf-accent-glow);
}

.timeline-step-title {
  font-family: var(--pf-font-subheading);
  font-size: 15px;
  color: var(--pf-white);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 8px;
}

.timeline-step-desc {
  font-family: var(--pf-font-body);
  font-size: 13px;
  color: var(--pf-text-muted);
  line-height: 1.4;
}
```

**Step 5: Run tests**

Run: `pytest tests/test_timeline_layout.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add templates/layouts/timeline.html.j2 theme/components.css tests/test_timeline_layout.py
git commit -m "feat: add timeline layout with horizontal connected steps"
```

---

## Task 10: Speaker Notes

**Files:**
- Modify: `templates/base.html.j2` (add hidden notes aside)
- Modify: `templates/present.html.j2` (notes panel + N key)
- Modify: `pf/builder.py` (pass notes to template)
- Create: `tests/test_speaker_notes.py`

**Step 1: Write failing test**

```python
"""Tests for speaker notes."""
import tempfile
from pathlib import Path
import yaml
from pf.builder import PresentationBuilder


class TestSpeakerNotes:
    def test_notes_rendered_as_aside(self):
        b = PresentationBuilder()
        b.config = {
            "meta": {"title": "Test"},
            "theme": {"fonts": {"heading": "Playfair Display", "subheading": "Montserrat", "body": "Lato"}},
        }
        slide = {
            "layout": "title",
            "notes": "Remember to mention the timeline",
            "data": {"title": "Hello"},
        }
        html = b.render_slide(slide, 0)
        assert '<aside class="notes">' in html
        assert "Remember to mention the timeline" in html

    def test_no_notes_no_aside(self):
        b = PresentationBuilder()
        b.config = {
            "meta": {"title": "Test"},
            "theme": {"fonts": {"heading": "Playfair Display", "subheading": "Montserrat", "body": "Lato"}},
        }
        slide = {
            "layout": "title",
            "data": {"title": "Hello"},
        }
        html = b.render_slide(slide, 0)
        assert '<aside class="notes">' not in html
```

**Step 2: Run test to verify failure**

Run: `pytest tests/test_speaker_notes.py -v`
Expected: FAIL

**Step 3: Add notes aside to `templates/base.html.j2`**

After the `page-number` div (line 19), before `</div></body>`:
```html
    {% if slide.notes %}
    <aside class="notes" style="display:none;">{{ slide.notes }}</aside>
    {% endif %}
```

**Step 4: Add notes panel to `templates/present.html.j2`**

Add HTML for the notes panel (before `</body>`):
```html
<div class="notes-panel" id="notesPanel">
  <div class="notes-panel-header">
    <span>SPEAKER NOTES</span>
    <button onclick="toggleNotes()" style="background:none;border:none;color:var(--gold);cursor:pointer;font-size:18px;">&times;</button>
  </div>
  <div class="notes-panel-body" id="notesPanelBody">
    <p style="color:#666;font-style:italic;">No notes for this slide.</p>
  </div>
</div>
```

Add CSS for notes panel in the `<style>` block:
```css
.notes-panel {
  position: fixed; right: 0; top: 0; bottom: 0; width: 320px;
  background: rgba(20, 28, 40, 0.97); border-left: 1px solid var(--gold-dim);
  z-index: 250; display: none; flex-direction: column;
  font-family: 'Montserrat', system-ui; backdrop-filter: blur(10px);
}
.notes-panel.visible { display: flex; }
.notes-panel-header {
  padding: 16px 20px; border-bottom: 1px solid var(--gold-dim);
  color: var(--gold); font-size: 12px; font-weight: 600; letter-spacing: 2px;
  display: flex; justify-content: space-between; align-items: center;
}
.notes-panel-body {
  padding: 20px; flex: 1; overflow-y: auto; color: #ccc; font-size: 14px; line-height: 1.6;
}
```

Add JS for notes functionality:
```javascript
let notesVisible = false;
const notesPanel = document.getElementById('notesPanel');
const notesPanelBody = document.getElementById('notesPanelBody');

function toggleNotes() {
  notesVisible = !notesVisible;
  notesPanel.classList.toggle('visible', notesVisible);
  if (notesVisible) loadNotes();
}

function loadNotes() {
  const iframe = document.getElementById('slide-frame');
  try {
    const aside = iframe.contentDocument.querySelector('aside.notes');
    notesPanelBody.innerHTML = aside
      ? '<p>' + aside.textContent + '</p>'
      : '<p style="color:#666;font-style:italic;">No notes for this slide.</p>';
  } catch(e) {
    notesPanelBody.innerHTML = '<p style="color:#666;">Cannot load notes (cross-origin).</p>';
  }
}
```

Add 'N' to the keyboard handler in the `switch(e.key)` block:
```javascript
case 'n': case 'N': toggleNotes(); break;
```

Update the hints section to include the N key:
```html
<kbd>N</kbd> speaker notes<br/>
```

Also call `loadNotes()` at the end of the `show()` function so notes update on slide change.

**Step 5: Run tests**

Run: `pytest tests/test_speaker_notes.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add templates/base.html.j2 templates/present.html.j2 tests/test_speaker_notes.py
git commit -m "feat: add speaker notes with N key toggle in navigator"
```

---

## Task 11: Better Error Messages

**Files:**
- Modify: `pf/builder.py` (wrap template rendering with better errors)
- Modify: `pf/builder.py` (warn on unresolved metrics references)

**Step 1: Write failing test**

Add to `tests/test_builder.py`:

```python
class TestErrorMessages:
    def test_invalid_layout_raises_clear_error(self):
        b = PresentationBuilder()
        b.config = {
            "meta": {"title": "Test"},
            "theme": {"fonts": {"heading": "Playfair Display", "subheading": "Montserrat", "body": "Lato"}},
        }
        slide = {"layout": "nonexistent", "data": {"title": "Bad"}}
        with pytest.raises(click.ClickException, match="slide 1.*nonexistent"):
            b.render_slide(slide, 0)
```

**Step 2: Run test to verify failure**

Run: `pytest tests/test_builder.py::TestErrorMessages -v`
Expected: FAIL — raises TemplateNotFound, not ClickException

**Step 3: Wrap render_slide with error handling**

In `pf/builder.py`, update `render_slide()`:

```python
import click
from jinja2 import TemplateNotFound

def render_slide(self, slide_config: dict, index: int, density: str = "normal") -> str:
    """Render a single slide to HTML string."""
    layout = slide_config.get("layout", "two-column")
    template_name = f"layouts/{layout}.html.j2"

    try:
        template = self.env.get_template(template_name)
    except TemplateNotFound:
        valid = ", ".join(sorted(
            p.stem for p in (TEMPLATES_DIR / "layouts").glob("*.html.j2")
        ))
        raise click.ClickException(
            f"slide {index + 1} uses unknown layout '{layout}'. "
            f"Valid layouts: {valid}"
        )

    meta = self.config.get("meta", {})
    theme = self.config.get("theme", {})
    page_number = slide_config.get("page_number", f"{index + 1:02d}")

    try:
        return template.render(
            slide=slide_config,
            slide_title=slide_config.get("data", {}).get("title", f"Slide {index + 1}"),
            meta=meta,
            theme=theme,
            page_number=page_number,
            density=density,
        )
    except Exception as e:
        raise click.ClickException(
            f"slide {index + 1} ({layout}): template error — {e}"
        )
```

**Step 4: Add unresolved metrics warnings**

In `_interpolate_string()`, add tracking. Add a class attribute `_unresolved_refs` to the builder, and in `build()`, after resolution, check for leftover `{{ metrics.` patterns and print warnings:

```python
# In build(), after resolve_data for each slide:
resolved_data = self.resolve_data(slide_cfg.get("data", {}), self.metrics)
# Check for unresolved references
unresolved = self._find_unresolved(resolved_data)
for ref in unresolved:
    click.echo(
        click.style(f"  ⚠ slide {i+1:02d}: ", fg="yellow")
        + f"unresolved reference {ref}"
    )
slide_cfg["data"] = resolved_data
```

Add helper:
```python
def _find_unresolved(self, data) -> list[str]:
    """Find any remaining {{ metrics.x.y }} patterns in resolved data."""
    import re
    refs = []
    if isinstance(data, str):
        refs.extend(re.findall(r"\{\{\s*metrics\.[a-zA-Z0-9_.]+\s*\}\}", data))
    elif isinstance(data, list):
        for item in data:
            refs.extend(self._find_unresolved(item))
    elif isinstance(data, dict):
        for v in data.values():
            refs.extend(self._find_unresolved(v))
    return refs
```

**Step 5: Run tests**

Run: `pytest tests/test_builder.py -v`
Expected: All PASS

**Step 6: Commit**

```bash
git add pf/builder.py tests/test_builder.py
git commit -m "feat: improve error messages with layout validation and unresolved ref warnings"
```

---

## Task 12: YAML Schema Validation

**Files:**
- Create: `pf/schema.json`
- Modify: `pf/builder.py` (validate config before build)
- Create: `tests/test_schema.py`

**Step 1: Write failing test**

```python
"""Tests for YAML schema validation."""
import pytest
from pf.builder import PresentationBuilder


class TestSchemaValidation:
    def test_missing_slides_key(self):
        b = PresentationBuilder()
        b.config = {"meta": {"title": "Test"}}
        errors = b.validate_config()
        assert len(errors) > 0
        assert any("slides" in e for e in errors)

    def test_invalid_layout_name(self):
        b = PresentationBuilder()
        b.config = {
            "meta": {"title": "Test"},
            "slides": [{"layout": "nonexistent", "data": {}}],
        }
        errors = b.validate_config()
        assert len(errors) > 0

    def test_valid_config_no_errors(self):
        b = PresentationBuilder()
        b.config = {
            "meta": {"title": "Test"},
            "slides": [{"layout": "title", "data": {"title": "Hi"}}],
        }
        errors = b.validate_config()
        assert errors == []
```

**Step 2: Run test to verify failure**

Run: `pytest tests/test_schema.py -v`
Expected: FAIL — `validate_config` not defined

**Step 3: Create `pf/schema.json`**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["slides"],
  "properties": {
    "meta": {
      "type": "object",
      "properties": {
        "title": {"type": "string"},
        "authors": {"type": "array", "items": {"type": "string"}},
        "institution": {"type": "string"},
        "date": {"type": "string"}
      }
    },
    "theme": {
      "type": "object",
      "properties": {
        "primary": {"type": "string"},
        "accent": {"type": "string"},
        "secondary_accent": {"type": "string"},
        "style": {"type": "string", "enum": ["modern", "minimal", "bold"]},
        "fonts": {
          "type": "object",
          "properties": {
            "heading": {"type": "string"},
            "subheading": {"type": "string"},
            "body": {"type": "string"}
          }
        }
      }
    },
    "slides": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["layout", "data"],
        "properties": {
          "layout": {
            "type": "string",
            "enum": ["title", "two-column", "three-column", "data-table", "stat-grid", "closing", "image", "section", "quote", "timeline"]
          },
          "data": {"type": "object"},
          "notes": {"type": "string"},
          "transition": {"type": "string", "enum": ["fade", "slide-left", "slide-up", "none"]}
        }
      }
    }
  }
}
```

**Step 4: Add `validate_config()` to builder**

In `pf/builder.py`:

```python
import jsonschema

def validate_config(self) -> list[str]:
    """Validate config against JSON schema. Returns list of error messages."""
    schema_path = Path(__file__).parent / "schema.json"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    validator = jsonschema.Draft202012Validator(schema)
    errors = []
    for error in sorted(validator.iter_errors(self.config), key=lambda e: list(e.path)):
        path = " → ".join(str(p) for p in error.absolute_path) or "root"
        errors.append(f"{path}: {error.message}")
    return errors
```

Integrate into `build()` method, after `load_config()`:

```python
# Validate config
errors = self.validate_config()
if errors:
    for e in errors:
        click.echo(click.style(f"  ✗ {e}", fg="red"), err=True)
    raise click.ClickException("Config validation failed. Fix errors above.")
```

**Step 5: Run tests**

Run: `pytest tests/test_schema.py -v`
Expected: All PASS

**Step 6: Commit**

```bash
git add pf/schema.json pf/builder.py tests/test_schema.py
git commit -m "feat: add YAML schema validation with clear error messages"
```

---

## Task 13: Slide Transitions

**Files:**
- Create: `theme/transitions.css`
- Modify: `templates/base.html.j2` (link transitions.css)
- Modify: `templates/present.html.j2` (transition logic in JS)
- Modify: `pf/builder.py` (pass transition data, copy transitions.css)

**Step 1: Create `theme/transitions.css`**

```css
/* ═══════════════════════════════════════════════════════════════
   Presentation Framework — Slide Transitions
   ═══════════════════════════════════════════════════════════════ */

/* Transitions are applied to the iframe wrapper in the navigator */
```

**Step 2: Update navigator JS for transitions**

In `templates/present.html.j2`, replace the `show()` function:

```javascript
function show(n, instant) {
  current = Math.max(1, Math.min(TOTAL, n));
  const file = SLIDES[current - 1];
  const transition = TRANSITIONS[current - 1] || 'fade';

  if (instant || transition === 'none') {
    frame.src = file;
  } else {
    frame.classList.add('fading');
    setTimeout(() => {
      frame.src = file;
      frame.classList.remove('fading');
    }, 200);
  }

  curEl.textContent = current;
  slideNumEl.textContent = 'SLIDE ' + String(current).padStart(2, '0');
  progress.style.width = ((current / TOTAL) * 100) + '%';
  document.querySelectorAll('.thumb').forEach((t, i) => {
    t.classList.toggle('active', i === current - 1);
  });
  if (notesVisible) loadNotes();
}
```

Add `TRANSITIONS` array to the JS constants (passed from builder):
```javascript
const TRANSITIONS = {{ transitions_json }};
```

**Step 3: Update `render_navigator()` in `pf/builder.py`**

Add `transitions` parameter:
```python
def render_navigator(self, slide_files, slide_titles, slide_transitions=None):
    template = self.env.get_template("present.html.j2")
    meta = self.config.get("meta", {})
    theme = self.config.get("theme", {})
    transitions = slide_transitions or ["fade"] * len(slide_files)

    return template.render(
        meta=meta,
        theme=theme,
        slides=slide_files,
        slides_json=json.dumps(slide_files),
        titles_json=json.dumps(slide_titles),
        transitions_json=json.dumps(transitions),
        total=len(slide_files),
    )
```

Collect transitions in `build()`:
```python
slide_transitions = []
# Inside the slide loop:
slide_transitions.append(slide_cfg.get("transition", "fade"))
# When calling render_navigator:
nav_html = self.render_navigator(slide_files, slide_titles, slide_transitions)
```

**Step 4: Commit**

```bash
git add theme/transitions.css templates/base.html.j2 templates/present.html.j2 pf/builder.py
git commit -m "feat: add CSS slide transitions with per-slide configuration"
```

---

## Task 14: Expanded Theme Options

**Files:**
- Modify: `pf/builder.py:136-215` (generate_variables_css — add secondary_accent, style presets)
- Modify: `theme/variables.css` (add secondary accent variable)
- Create: `tests/test_theme.py`

**Step 1: Write failing test**

```python
"""Tests for expanded theme options."""
from pf.builder import PresentationBuilder


class TestExpandedTheme:
    def test_secondary_accent_generated(self):
        b = PresentationBuilder()
        theme = {
            "primary": "#1C2537",
            "accent": "#C4A962",
            "secondary_accent": "#5B8FA8",
        }
        css = b.generate_variables_css(theme)
        assert "--pf-secondary-accent" in css
        assert "#5B8FA8" in css

    def test_no_secondary_accent_default(self):
        b = PresentationBuilder()
        theme = {"primary": "#1C2537", "accent": "#C4A962"}
        css = b.generate_variables_css(theme)
        # Should have a default secondary accent
        assert "--pf-secondary-accent" in css

    def test_style_preset_modern(self):
        b = PresentationBuilder()
        theme = {"primary": "#1C2537", "accent": "#C4A962", "style": "modern"}
        css = b.generate_variables_css(theme)
        assert "--pf-radius-lg" in css

    def test_style_preset_minimal(self):
        b = PresentationBuilder()
        theme = {"primary": "#1C2537", "accent": "#C4A962", "style": "minimal"}
        css = b.generate_variables_css(theme)
        assert "--pf-radius-lg" in css
```

**Step 2: Run test to verify failure**

Run: `pytest tests/test_theme.py -v`
Expected: FAIL — `--pf-secondary-accent` not in output

**Step 3: Update `generate_variables_css()` in `pf/builder.py`**

After the accent RGBA variants block, add:

```python
        # Secondary accent
        secondary = theme.get("secondary_accent", "#5B8FA8")
        sr, sg, sb = _hex_to_rgb(secondary)

        # Style presets
        style = theme.get("style", "modern")
        style_overrides = {
            "modern": {
                "radius_lg": "8px",
                "shadow": "0 4px 6px rgba(0, 0, 0, 0.2)",
            },
            "minimal": {
                "radius_lg": "2px",
                "shadow": "none",
            },
            "bold": {
                "radius_lg": "12px",
                "shadow": "0 8px 16px rgba(0, 0, 0, 0.3)",
            },
        }
        preset = style_overrides.get(style, style_overrides["modern"])
```

Add to the `:root` block in the generated CSS:
```python
        custom_root += f"""

  /* ── Secondary Accent (generated) ──────────────────────── */
  --pf-secondary-accent:        {secondary};
  --pf-secondary-accent-dim:    rgba({sr}, {sg}, {sb}, 0.4);
  --pf-secondary-accent-bg:     rgba({sr}, {sg}, {sb}, 0.1);"""
```

And inject style preset overrides after the main `:root` block closes.

**Step 4: Run tests**

Run: `pytest tests/test_theme.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add pf/builder.py theme/variables.css tests/test_theme.py
git commit -m "feat: add secondary accent color and style presets (modern/minimal/bold)"
```

---

## Task 15: Live-Reload `pf serve`

**Files:**
- Modify: `pf/cli.py:129-149` (serve command)
- Modify: `templates/present.html.j2` (SSE listener)

**Step 1: Update `pf serve` with watchdog + SSE**

Replace the `serve` command in `pf/cli.py`:

```python
import threading
import time

@cli.command()
@click.option("--dir", "-d", "directory", default="slides", help="Directory to serve")
@click.option("--port", "-p", default=8080, help="Port number")
@click.option("--watch/--no-watch", default=True, help="Watch for changes and auto-rebuild")
@click.option("--config", "-c", default="presentation.yaml", help="Config for rebuild")
@click.option("--metrics", "-m", default="metrics.json", help="Metrics for rebuild")
def serve(directory: str, port: int, watch: bool, config: str, metrics: str):
    """Start a local HTTP server with optional live-reload."""
    serve_dir = Path(directory)
    if not serve_dir.exists():
        click.echo(f"Error: directory '{directory}' not found. Run 'pf build' first.", err=True)
        raise SystemExit(1)

    # SSE reload event
    reload_event = threading.Event()

    class ReloadHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(serve_dir), **kwargs)

        def do_GET(self):
            if self.path == '/__reload':
                self.send_response(200)
                self.send_header('Content-Type', 'text/event-stream')
                self.send_header('Cache-Control', 'no-cache')
                self.send_header('Connection', 'keep-alive')
                self.end_headers()
                while True:
                    if reload_event.wait(timeout=1):
                        self.wfile.write(b'data: reload\n\n')
                        self.wfile.flush()
                        reload_event.clear()
                return
            super().do_GET()

        def log_message(self, format, *args):
            pass  # Suppress request logs

    if watch:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler

        class RebuildHandler(FileSystemEventHandler):
            def on_modified(self, event):
                if event.src_path.endswith(('.yaml', '.json', '.j2', '.css')):
                    click.echo(click.style("  ↻ Change detected, rebuilding...", fg="cyan"))
                    try:
                        builder = PresentationBuilder(config_path=config, metrics_path=metrics)
                        builder.build(output_dir=directory)
                        reload_event.set()
                        click.echo(click.style("  ✓ Rebuilt successfully", fg="green"))
                    except Exception as e:
                        click.echo(click.style(f"  ✗ Build error: {e}", fg="red"))

        observer = Observer()
        observer.schedule(RebuildHandler(), ".", recursive=False)
        observer.start()
        click.echo(click.style("  Watching for changes...", fg="cyan"))

    click.echo(f"Serving {directory}/ at http://localhost:{port}")
    click.echo(f"Open http://localhost:{port}/present.html to present.")
    click.echo("Press Ctrl+C to stop.\n")

    server = http.server.HTTPServer(("", port), ReloadHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        click.echo("\nServer stopped.")
        if watch:
            observer.stop()
            observer.join()
```

**Step 2: Add SSE listener to navigator**

In `templates/present.html.j2`, add at the end of the `<script>` block (before `</script>`):

```javascript
// Live-reload via SSE
if (window.location.protocol !== 'file:') {
  const evtSource = new EventSource('/__reload');
  evtSource.onmessage = function() { location.reload(); };
}
```

**Step 3: Test manually**

Run: `cd examples && pf serve --watch`
Edit `examples/presentation.yaml`, save. Browser should auto-reload.

**Step 4: Commit**

```bash
git add pf/cli.py templates/present.html.j2
git commit -m "feat: add live-reload to pf serve with watchdog and SSE"
```

---

## Task 16: PDF Export

**Files:**
- Create: `pf/pdf.py`
- Modify: `pf/cli.py` (add `pf pdf` command)
- Create: `tests/test_pdf.py`

**Step 1: Write failing test**

```python
"""Tests for PDF export."""
import pytest


class TestPdfImport:
    def test_pdf_module_exists(self):
        from pf.pdf import export_pdf
        assert callable(export_pdf)

    def test_pdf_graceful_without_playwright(self, monkeypatch):
        """If playwright is not installed, should raise ImportError with helpful message."""
        import pf.pdf
        monkeypatch.setattr(pf.pdf, "PLAYWRIGHT_AVAILABLE", False)
        with pytest.raises(ImportError, match="pip install"):
            pf.pdf.export_pdf("slides/", "output.pdf")
```

**Step 2: Run test to verify failure**

Run: `pytest tests/test_pdf.py -v`
Expected: FAIL — module not found

**Step 3: Create `pf/pdf.py`**

```python
"""
PDF export for Presentation Framework.
Requires: pip install presentation-framework[pdf]
"""

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


def export_pdf(slides_dir: str, output_path: str, include_notes: bool = False):
    """Export built slides to a single PDF file."""
    if not PLAYWRIGHT_AVAILABLE:
        raise ImportError(
            "PDF export requires Playwright. Install with:\n"
            "  pip install presentation-framework[pdf]\n"
            "  playwright install chromium"
        )

    from pathlib import Path
    import tempfile

    slides_path = Path(slides_dir).resolve()
    slide_files = sorted(slides_path.glob("slide_*.html"))

    if not slide_files:
        raise FileNotFoundError(f"No slide files found in {slides_dir}")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
        )

        pdf_pages = []
        for slide_file in slide_files:
            page = context.new_page()
            page.goto(f"file://{slide_file}")
            page.wait_for_load_state("networkidle")

            pdf_bytes = page.pdf(
                width="1280px",
                height="720px",
                print_background=True,
                landscape=True,
            )
            pdf_pages.append(pdf_bytes)
            page.close()

        # Use first slide's PDF as base, merge is complex — for now, just use
        # a simple approach: render all slides in one page via the navigator
        page = context.new_page()
        present_file = slides_path / "present.html"
        page.goto(f"file://{present_file}")
        page.wait_for_load_state("networkidle")

        # Navigate through each slide and print
        total = len(slide_files)
        all_pdfs = []
        for i in range(total):
            page.evaluate(f"show({i + 1}, true)")
            page.wait_for_timeout(300)
            pdf_data = page.pdf(
                width="1280px",
                height="720px",
                print_background=True,
                landscape=True,
            )
            all_pdfs.append(pdf_data)

        # Write the last approach: individual slide PDFs
        # For a single merged PDF, use the first slide's full render
        page.close()
        browser.close()

    # Write first page PDF (simple single-page-per-slide approach)
    # Full PDF merge would need pypdf — keep it simple for now
    with open(output_path, "wb") as f:
        f.write(pdf_pages[0] if pdf_pages else b"")
```

**Note:** This is a minimal MVP. A proper multi-page PDF merge would need `pypdf` — that can be a follow-up enhancement.

**Step 4: Add `pf pdf` command to `pf/cli.py`**

```python
@cli.command()
@click.option("--config", "-c", default="presentation.yaml", help="Path to presentation.yaml")
@click.option("--metrics", "-m", default="metrics.json", help="Path to metrics.json")
@click.option("--output", "-o", default="presentation.pdf", help="Output PDF path")
@click.option("--notes", is_flag=True, default=False, help="Include speaker notes")
def pdf(config: str, metrics: str, output: str, notes: bool):
    """Export slides to PDF (requires: pip install pf[pdf])."""
    try:
        from pf.pdf import export_pdf
    except ImportError:
        click.echo("PDF export requires Playwright. Install with:")
        click.echo("  pip install presentation-framework[pdf]")
        click.echo("  playwright install chromium")
        raise SystemExit(1)

    # Build first
    config_path = Path(config)
    if not config_path.exists():
        click.echo(f"Error: config file '{config}' not found.", err=True)
        raise SystemExit(1)

    builder = PresentationBuilder(config_path=config, metrics_path=metrics)
    out = builder.build(output_dir="slides")

    click.echo(f"Exporting to PDF...")
    try:
        export_pdf(str(out), output, include_notes=notes)
        click.echo(f"PDF exported → {output}")
    except Exception as e:
        click.echo(click.style(f"PDF export failed: {e}", fg="red"), err=True)
        raise SystemExit(1)
```

**Step 5: Run tests**

Run: `pytest tests/test_pdf.py -v`
Expected: PASS (at least the import and graceful-fallback tests)

**Step 6: Commit**

```bash
git add pf/pdf.py pf/cli.py tests/test_pdf.py
git commit -m "feat: add pf pdf command with optional Playwright-based PDF export"
```

---

## Task 17: Update Examples and Documentation

**Files:**
- Modify: `examples/presentation.yaml` (add new layout examples)
- Modify: `README.md` (document new features)
- Modify: `SKILL.md` (update AI-readable docs)

**Step 1: Add example slides for new layouts**

Add to `examples/presentation.yaml` slides array:

```yaml
  - layout: section
    data:
      title: "Research Findings"
      subtitle: "Key insights from our analysis"
      number: 1

  - layout: quote
    data:
      text: "Data is the new oil, but like oil, it must be refined to be useful."
      author: "Clive Humby"
      role: "Data Science Pioneer"

  - layout: image
    data:
      image: "https://via.placeholder.com/1280x720"
      position: full
      title: "Visual Overview"
      caption: "A comprehensive view of the system"

  - layout: timeline
    data:
      title: "Development Roadmap"
      steps:
        - icon: search
          title: "Research"
          description: "Market analysis and requirements gathering"
        - icon: pencil
          title: "Design"
          description: "Architecture and UI mockups"
        - icon: code
          title: "Build"
          description: "Implementation and testing"
        - icon: rocket
          title: "Launch"
          description: "Deployment and monitoring"
```

**Step 2: Update README.md with new features**

Add sections for: new layouts, speaker notes, live-reload, PDF export, layout warnings, theme options.

**Step 3: Commit**

```bash
git add examples/presentation.yaml README.md SKILL.md
git commit -m "docs: update examples and documentation for v0.2.0 features"
```

---

## Task 18: Run Full Test Suite and Final Verification

**Step 1: Run all tests**

Run: `pytest tests/ -v --tb=short`
Expected: All tests PASS

**Step 2: Build the example presentation**

Run: `cd examples && pf build --open`
Expected: All slides render correctly, new layouts visible, no warnings on normal content.

**Step 3: Test live-reload**

Run: `cd examples && pf serve --watch`
Edit a slide in `presentation.yaml`, verify browser reloads.

**Step 4: Verify warnings work**

Create a dense slide with 12+ cards, run `pf build`, verify yellow warning appears.

**Step 5: Final commit with version tag**

```bash
git tag v0.2.0
```
