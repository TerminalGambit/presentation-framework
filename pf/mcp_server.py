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
    """List all available slide layouts with descriptions.

    Returns core built-in layouts plus any plugin layouts discovered from
    installed packages (pf.layouts entry points) and local project directories.
    """
    from pf.registry import LayoutPlugin, PluginRegistry

    # Core layouts
    results: list[dict] = [
        {"name": name, "description": desc, "source": "core"}
        for name, desc in LAYOUT_DESCRIPTIONS.items()
    ]

    # Plugin layouts
    try:
        registry = PluginRegistry()
        registry.discover()
        for name in registry.layout_names:
            plugin = registry.get_layout(name)
            description = ""
            if isinstance(plugin, LayoutPlugin):
                description = plugin.description
            results.append({"name": name, "description": description, "source": "plugin"})
    except Exception:
        # Registry discovery is best-effort — never block the MCP tool
        pass

    return results


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


GENERATE_SYSTEM_PROMPT = """You are an expert presentation designer.
Generate a professional slide deck based on the user's prompt.

Available layouts (use a variety appropriate for the content):
- title: Opening slide with hero title, subtitle, tagline, feature icons, footer
- two-column: Main workhorse; typed content blocks (card, solution-box, stat-grid, table, dist-bars, val-bars, insight) in left/right columns
- three-column: Three-column comparisons; use columns list (not left/right)
- data-table: Benchmark/comparison tables with sections; use sections list
- stat-grid: KPI dashboard; use columns list (two columns of content blocks)
- chart: Interactive Plotly chart (bar, line, pie, scatter); requires labels and values lists
- section: Section divider between major topics; minimal — title, subtitle, optional number
- quote: Centered blockquote with author attribution
- image: Full-bleed or split image; requires image URL
- timeline: Horizontal step visualization (2–6 steps); each step has icon, title, description
- closing: Thank you / Q&A slide with contact pills

Style guidance:
- modern: clean, data-driven, minimal decoration
- minimal: whitespace-heavy, single focal point per slide
- bold: high contrast, large numbers, strong headlines

Length guidance (approximate slide counts, always include title + closing):
- short: ~5 slides (title + 3 content + closing)
- medium: ~8 slides (title + 6 content + closing)
- long: ~12 slides (title + 10 content + closing)

Rules:
1. ALWAYS start with a title slide and end with a closing slide.
2. Put ALL numerical data, lists, and benchmarks in the metrics dict — NEVER hardcode in yaml_config.
   Reference them in yaml_config via {{ metrics.key.subkey }} interpolation.
3. Choose diverse layouts — avoid using the same layout consecutively.
4. Keep slide content concise — each slide conveys ONE key idea.
5. The yaml_config must be valid YAML with a 'meta', 'theme', and 'slides' key.
6. The theme should use tasteful hex colors. Default: primary "#1E293B", accent "#6366F1".
"""


@mcp.tool()
def generate_presentation(
    prompt: str,
    style: str = "modern",
    length: str = "medium",
    provider: str = "anthropic/claude-sonnet-4-20250514",
) -> dict:
    """Generate a complete presentation from a natural language prompt.

    Uses an LLM (via the instructor library) to produce structured YAML
    config and metrics dict. Requires ``pip install 'pf[llm]'``.

    Args:
        prompt: Description of the presentation topic and content.
        style: Visual style — "modern", "minimal", or "bold".
        length: Approximate deck length — "short" (~5 slides),
                "medium" (~8 slides), or "long" (~12 slides).
        provider: LiteLLM-style provider string passed to
                  instructor.from_provider().

    Returns:
        dict with "yaml_config" (sanitized YAML string) and "metrics"
        (sanitized metrics dict), OR {"error": "..."} on failure.
    """
    try:
        import instructor  # type: ignore[import]
    except ImportError:
        return {"error": "LLM features require: pip install 'pf[llm]'"}

    import yaml

    from pf.llm_schemas import PresentationOutput
    from pf.sanitize import sanitize_slide_data

    user_message = (
        f"Create a {style} {length} presentation about:\n\n{prompt}\n\n"
        f"Return valid YAML for yaml_config and a flat metrics dict."
    )

    try:
        client = instructor.from_provider(provider, mode=instructor.Mode.TOOLS)
        result: PresentationOutput = client.create(
            response_model=PresentationOutput,
            max_tokens=4096,
            messages=[
                {"role": "system", "content": GENERATE_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
        )
    except Exception as e:
        return {"error": str(e)}

    # Sanitize yaml_config: parse → sanitize per-slide data → re-serialize
    try:
        config = yaml.safe_load(result.yaml_config)
        if isinstance(config, dict):
            slides = config.get("slides", [])
            for slide in slides:
                if isinstance(slide, dict) and "data" in slide:
                    slide["data"] = sanitize_slide_data(slide["data"])
            sanitized_yaml = yaml.dump(config, default_flow_style=False, sort_keys=False)
        else:
            # Unexpected structure — return raw yaml (safe fallback)
            sanitized_yaml = result.yaml_config
    except Exception:
        sanitized_yaml = result.yaml_config

    # Sanitize metrics dict directly
    raw_metrics = result.metrics if isinstance(result.metrics, dict) else {}
    sanitized_metrics = sanitize_slide_data(raw_metrics)

    return {"yaml_config": sanitized_yaml, "metrics": sanitized_metrics}


@mcp.tool()
def get_layout_schema(layout_name: str) -> dict:
    """Get the JSON Schema with constraints for a specific layout.

    Returns the Pydantic-generated JSON Schema for the named layout model,
    including maxItems, maxLength, and type constraints derived from
    LayoutAnalyzer size estimates. Useful for LLM structured-output
    prompting and validation.

    Args:
        layout_name: One of the 11 built-in layout names (e.g. "timeline",
                     "two-column", "data-table").

    Returns:
        JSON Schema dict with "properties", "required", etc., or
        {"error": "..."} for unknown layout names.
    """
    from pf.llm_schemas import get_layout_schema as _get_schema

    model = _get_schema(layout_name)
    if model is None:
        return {"error": f"Unknown layout: {layout_name}"}
    return model.model_json_schema()


MULTI_AGENT_WORKFLOW = """
Multi-Agent Presentation Workflow
=================================
1. RESEARCHER: Call generate_presentation(prompt, style, length) to create initial deck
2. REVIEWER: Call validate_config() on the generated YAML to check structure
3. OPTIMIZER: For each slide, call optimize_slide() to split overflowing content
4. BUILDER: Call build_presentation() to render the final HTML deck
5. AUDITOR: Call check_accessibility_output() to verify ARIA labels and alt text

Optional enhancement steps:
- Call suggest_layout() between steps 1-2 to refine slide selection
- Call get_layout_schema() to understand constraints before generation
- Call check_contrast() to verify theme accessibility
"""


@mcp.tool()
def optimize_slide(slide_yaml: str) -> dict:
    """Split an overflowing slide into multiple non-overflowing slides.

    Accepts a YAML string representing a single slide dict.
    Returns a dict with "slides" key containing a list of slide dicts,
    or "error" on failure.

    Args:
        slide_yaml: YAML string for a single slide (with "layout" and "data" keys).

    Returns:
        dict with "slides" (list of slide dicts), "count" (int), "was_split" (bool),
        or {"error": "..."} on invalid YAML or unexpected failure.
    """
    import yaml

    from pf.optimizer import split_slide

    try:
        slide_dict = yaml.safe_load(slide_yaml)
    except yaml.YAMLError as e:
        return {"error": f"Invalid YAML: {e}"}

    try:
        result = split_slide(slide_dict)
        return {
            "slides": result,
            "count": len(result),
            "was_split": len(result) > 1,
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def suggest_layout(
    slides_yaml: str,
    topic: str = "",
    count: int = 3,
    provider: str = "anthropic/claude-sonnet-4-20250514",
) -> dict:
    """Suggest next slides for a partial presentation deck.

    Given the current slides (as YAML) and an optional topic, suggests
    the next N slides with layout type and content outline.

    Requires ``pip install 'pf[llm]'`` for LLM-based suggestions.

    Args:
        slides_yaml: YAML string of the current slides list.
        topic: Optional topic/subject for the presentation.
        count: Number of slide suggestions to return (1-5).
        provider: LiteLLM-style provider string for instructor.

    Returns:
        dict with "suggestions" list (each has "layout", "title", "reasoning"),
        or {"error": "..."} on failure.
    """
    try:
        import instructor  # type: ignore[import]
    except ImportError:
        return {"error": "LLM features require: pip install 'pf[llm]'"}

    from pydantic import BaseModel, Field

    class SlideSuggestion(BaseModel):
        layout: str = Field(description="Layout name from available layouts")
        title: str = Field(max_length=80)
        reasoning: str = Field(
            max_length=200,
            description="Why this slide follows logically from the current deck",
        )

    class SuggestionList(BaseModel):
        suggestions: list[SlideSuggestion] = Field(max_length=5)

    available_layouts = ", ".join(LAYOUT_DESCRIPTIONS.keys())
    topic_line = f"Topic: {topic}\n\n" if topic else ""

    suggestion_prompt = (
        f"{topic_line}"
        f"Current deck slides (YAML):\n{slides_yaml}\n\n"
        f"Available layout types: {available_layouts}\n\n"
        f"Suggest the next {count} slides that would logically follow this deck. "
        f"Each suggestion must use one of the available layout types and explain "
        f"why it follows naturally from the existing content flow."
    )

    try:
        client = instructor.from_provider(provider, mode=instructor.Mode.TOOLS)
        result: SuggestionList = client.create(
            response_model=SuggestionList,
            max_tokens=1024,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert presentation designer. "
                        "Suggest logical next slides based on the current deck content."
                    ),
                },
                {"role": "user", "content": suggestion_prompt},
            ],
        )
        return {"suggestions": [s.model_dump() for s in result.suggestions]}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def check_accessibility_output(output_dir: str) -> dict:
    """Audit built slide HTML files for accessibility issues.

    Scans all slide_*.html files in the output directory for missing alt
    attributes, missing ARIA labels, and other a11y problems.
    Returns a dict with "warnings" list and "pass" boolean.

    Args:
        output_dir: Path to the directory containing built slide HTML files.

    Returns:
        dict with "pass" (bool), "warning_count" (int), "warnings" (list of dicts),
        or {"error": "..."} if the directory does not exist.
    """
    from pathlib import Path as _Path

    from pf.accessibility import check_slide_dir

    if not _Path(output_dir).is_dir():
        return {"error": f"Output directory not found: {output_dir}"}

    try:
        warnings = check_slide_dir(output_dir)
        warning_dicts = [
            {
                "file": w.file,
                "element": w.element,
                "issue": w.issue,
                "suggestion": w.suggestion,
                "severity": w.severity,
            }
            for w in warnings
        ]
        return {
            "pass": len(warnings) == 0,
            "warning_count": len(warnings),
            "warnings": warning_dicts,
        }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    mcp.run()
