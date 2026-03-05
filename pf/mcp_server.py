"""
MCP server for the Presentation Framework.

Exposes build, validate, contrast-check, layout-list, and init tools
via FastMCP (stdio transport). Run with: python -m pf.mcp_server
"""

import contextlib
import io
import json
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("presentation-framework")


@mcp.tool()
def build_presentation(
    config_path: str,
    metrics_path: str = "metrics.json",
    output_dir: str = "slides",
) -> dict:
    """Build an HTML slide deck from a presentation.yaml and metrics.json.

    Returns slide count, layout warnings, and contrast warnings.
    """
    from pf.builder import PresentationBuilder

    config = Path(config_path)
    if not config.exists():
        return {"error": f"Config file not found: {config_path}"}

    try:
        builder = PresentationBuilder(
            config_path=config_path, metrics_path=metrics_path
        )
        # Capture stdout — builder.build() uses click.echo() which would
        # corrupt the stdio JSON-RPC channel.
        stdout_capture = io.StringIO()
        with contextlib.redirect_stdout(stdout_capture):
            out = builder.build(output_dir=output_dir)

        slide_count = len(list(out.glob("slide_*.html")))
        warnings = [
            {
                "slide": w["slide_index"] + 1,
                "layout": w["layout"],
                "column": w["column"],
                "overflow_pct": w["overflow_pct"],
            }
            for w in getattr(builder, "_warnings", [])
        ]
        contrast_warnings = getattr(builder, "_contrast_warnings", [])

        return {
            "output_dir": str(out),
            "slide_count": slide_count,
            "warnings": warnings,
            "contrast_warnings": contrast_warnings,
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def validate_config(config_path: str) -> dict:
    """Validate a presentation.yaml against the JSON schema.

    Returns {valid: true} or {valid: false, errors: [...]}.
    """
    from pf.builder import PresentationBuilder

    config = Path(config_path)
    if not config.exists():
        return {"error": f"Config file not found: {config_path}"}

    try:
        builder = PresentationBuilder(config_path=config_path)
        builder.load_config()
        errors = builder.validate_config()
        if errors:
            return {"valid": False, "errors": errors}
        return {"valid": True, "errors": []}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def check_contrast(
    primary: str,
    accent: str,
    secondary_accent: str | None = None,
) -> dict:
    """Check WCAG 2.1 contrast ratios for a theme color combination.

    Returns pass/fail status, warnings, and individual ratios.
    """
    from pf.contrast import check_contrast as _check_contrast
    from pf.contrast import contrast_ratio

    try:
        warnings = _check_contrast(primary, accent, secondary_accent)

        ratios = {
            "accent_on_primary": contrast_ratio(accent, primary),
            "text_on_primary": contrast_ratio("#e0e0e0", primary),
        }
        if secondary_accent:
            ratios["secondary_on_primary"] = contrast_ratio(
                secondary_accent, primary
            )

        return {
            "passes": len(warnings) == 0,
            "warnings": warnings,
            "ratios": ratios,
        }
    except Exception as e:
        return {"error": str(e)}


LAYOUT_DESCRIPTIONS = {
    "title": "Opening slide with title, subtitle, tagline, and feature icons",
    "two-column": "Two-column layout for side-by-side content blocks",
    "three-column": "Three-column layout for comparing items or categories",
    "data-table": "Tabular data display with headers and rows",
    "stat-grid": "Grid of key statistics with labels and values",
    "closing": "Closing slide with thank-you message and contact info",
    "image": "Full or partial image with optional caption overlay",
    "section": "Section divider with large heading and optional subtitle",
    "quote": "Blockquote display with attribution",
    "timeline": "Chronological sequence of events or milestones",
    "chart": "Interactive Plotly chart (requires theme.charts: true)",
}

LAYOUT_EXAMPLES = {
    "title": {
        "description": "Opening slide with title, subtitle, tagline, feature icons, and footer",
        "yaml_example": """- layout: title
  data:
    title: "Deck Title"                  # Required
    subtitle: "Subtitle"                 # Optional
    tagline: "One-line description"      # Optional
    quote: "\\\"Quoted text.\\\""        # Optional
    title_size: "120px"                  # Optional (default 120px)
    features:                            # Optional — bottom grid
      - icon: gem                        # FontAwesome icon name
        label: "Feature Label"
        sub: "Description"
    footer: "Author — Institution"       # Optional""",
    },
    "two-column": {
        "description": "Two-column grid with typed content blocks (cards, tables, stats, bars, insights)",
        "yaml_example": """- layout: two-column
  data:
    title: "Slide Title"                 # Required
    subtitle: "Optional subtitle"
    column_ratio: "2fr 1fr"              # Optional CSS grid ratio
    left:                                # List of content blocks
      - type: card
        icon: layer-group
        title: "Card Title"
        text: "Card body text."
        bullets:
          - "Bullet with <strong>HTML</strong>"
      - type: stat-grid
        cols: 2
        stats:
          - { value: "128", label: "Assets" }
          - { value: "9", label: "Categories" }
      - type: insight
        text: "<strong>Key insight</strong> — explanation."
        icon: lightbulb
    right:
      - type: solution-box
        badge: "Badge"
        title: "Box Title"
        icon: gem
        items:
          - "Checklist item 1"
          - "Checklist item 2"
# Block types: card, solution-box, stat-grid, table, dist-bars,
#   val-bars, unit-grid, insight, value-prop, takeaway, html""",
    },
    "three-column": {
        "description": "Three-column grid using columns list (not left/right)",
        "yaml_example": """- layout: three-column
  data:
    title: "Slide Title"
    column_ratio: "1fr 1fr 1fr"          # Optional
    columns:
      - # Column 1
        - type: card
          header: "Header"
          icon: chart-line
          content: "<p>HTML content</p>"
      - # Column 2
        - type: stat-grid
          stats:
            - { value: "42", label: "Things" }
      - # Column 3
        - type: image
          src: "path/to/image.png"
          alt: "Description"
# Block types: card, stat-grid, table, val-bars, insight, image, html""",
    },
    "data-table": {
        "description": "Two-section layout for benchmarks, tables, and analysis",
        "yaml_example": """- layout: data-table
  data:
    title: "Benchmark Results"
    subtitle: "Comparison"
    sections:
      - section_title: "Section A"
        section_icon: "vector-square"
        table:
          headers: ["Model", "Score"]
          rows:
            - ["Model A", "0.95"]
            - ["Model B", "0.87"]
          winner_rows: [0]
          footnote: "Note text"
        insight:
          text: "Key finding."
          icon: lightbulb""",
    },
    "stat-grid": {
        "description": "Two-column KPI dashboard with stat boxes, cards, and insights",
        "yaml_example": """- layout: stat-grid
  data:
    title: "Key Metrics"
    column_ratio: "1fr 1fr"
    columns:
      - # Column 1
        - type: stat-grid
          cols: 2
          stats:
            - { value: "128", label: "Total" }
            - { value: "9", label: "Categories" }
      - # Column 2
        - type: card
          header: "Details"
          icon: info-circle
          items:
            - "Item one"
            - "Item two" """,
    },
    "chart": {
        "description": "Interactive Plotly chart (requires theme.charts: true)",
        "yaml_example": """- layout: chart
  data:
    title: "Revenue by Quarter"          # Optional
    subtitle: "FY 2025-2026"             # Optional
    chart_type: bar                      # bar, line, pie, scatter
    source: "{{ metrics.revenue }}"      # Metrics ref OR inline labels/values
# Inline alternative:
#   labels: ["Q1", "Q2", "Q3", "Q4"]
#   values: [10, 20, 30, 40]
# Multi-series:
#   series:
#     - name: "Product A"
#       values: [10, 20, 30, 40]""",
    },
    "closing": {
        "description": "Closing slide with title, info pills, and footer",
        "yaml_example": """- layout: closing
  data:
    title: "Thank You"
    subtitle: "Questions & Discussion"
    title_size: "72px"                   # Optional
    info_items:                          # Optional
      - type: pill
        icon: "fa-brands fa-github"      # Full FA class for pills
        text: "github.com/user/repo"
      - type: info
        icon: "fa-solid fa-graduation-cap"
        text: "Institution"
    footer: "Footer text" """,
    },
    "image": {
        "description": "Full-bleed or split image with optional title and caption",
        "yaml_example": """- layout: image
  data:
    image: "https://example.com/photo.jpg"  # Required
    position: full                           # full or split
    title: "Image Title"                     # Optional
    caption: "Description"                   # Optional""",
    },
    "section": {
        "description": "Section divider with large title, subtitle, and optional number",
        "yaml_example": """- layout: section
  data:
    title: "Part Two"                    # Required
    subtitle: "Deep Dive"                # Optional
    number: 2                            # Optional""",
    },
    "quote": {
        "description": "Centered quotation with decorative marks and attribution",
        "yaml_example": """- layout: quote
  data:
    text: "The only way to do great work is to love what you do."  # Required
    author: "Steve Jobs"                 # Optional
    role: "Co-founder, Apple"            # Optional""",
    },
    "timeline": {
        "description": "Horizontal step visualization with icons (2-6 steps)",
        "yaml_example": """- layout: timeline
  data:
    title: "Project Roadmap"             # Required
    steps:                               # Required (2-6 steps)
      - icon: search
        title: "Research"
        description: "Gather requirements"
      - icon: code
        title: "Build"
        description: "Implementation"
      - icon: rocket
        title: "Launch"
        description: "Go live" """,
    },
}


@mcp.tool()
def list_layouts() -> list[dict]:
    """List all available slide layouts with descriptions."""
    return [
        {"name": name, "description": desc}
        for name, desc in LAYOUT_DESCRIPTIONS.items()
    ]


@mcp.tool()
def get_layout_example(layout_name: str) -> dict:
    """Get the YAML data shape and example for a specific slide layout.

    Returns the layout name, description, and a complete YAML example
    showing all available fields. Use this to understand what data
    a layout expects before writing presentation.yaml.
    """
    example = LAYOUT_EXAMPLES.get(layout_name)
    if not example:
        valid = ", ".join(sorted(LAYOUT_EXAMPLES.keys()))
        return {"error": f"Unknown layout '{layout_name}'. Valid layouts: {valid}"}
    return {
        "name": layout_name,
        "description": example["description"],
        "yaml_example": example["yaml_example"],
    }


@mcp.tool()
def init_presentation(name: str, directory: str = ".") -> dict:
    """Scaffold a new presentation project with starter config and metrics.

    Creates <directory>/<name>/ with presentation.yaml, metrics.json, and slides/.
    """
    import yaml

    from pf.cli import STARTER_CONFIG, STARTER_METRICS

    project_dir = Path(directory) / name
    if project_dir.exists():
        return {"error": f"Directory already exists: {project_dir}"}

    try:
        project_dir.mkdir(parents=True)
        (project_dir / "slides").mkdir()

        config_path = project_dir / "presentation.yaml"
        config_path.write_text(
            yaml.dump(STARTER_CONFIG, default_flow_style=False, sort_keys=False),
            encoding="utf-8",
        )

        metrics_path = project_dir / "metrics.json"
        metrics_path.write_text(
            json.dumps(STARTER_METRICS, indent=2), encoding="utf-8"
        )

        return {
            "project_dir": str(project_dir),
            "files_created": [
                str(config_path),
                str(metrics_path),
                str(project_dir / "slides"),
            ],
        }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    mcp.run()
