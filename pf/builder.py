"""
PresentationBuilder — reads presentation.yaml + metrics.json and generates
a complete HTML slide deck using Jinja2 templates and a shared CSS theme.
"""

import json
import re
import shutil
from pathlib import Path

import click
import jsonschema
import yaml
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from pf.analyzer import LayoutAnalyzer
from pf.contrast import check_contrast


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert '#RRGGBB' to (r, g, b) ints."""
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _darken_hex(hex_color: str, factor: float = 0.4) -> str:
    """Darken a hex color by a factor (0 = black, 1 = unchanged)."""
    r, g, b = _hex_to_rgb(hex_color)
    return f"#{int(r * factor):02x}{int(g * factor):02x}{int(b * factor):02x}"

# Root of the presentation-framework package
PACKAGE_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = PACKAGE_ROOT / "templates"
THEME_DIR = PACKAGE_ROOT / "theme"


class PresentationBuilder:
    """Build HTML presentations from YAML config + JSON metrics."""

    def __init__(self, config_path: str = "presentation.yaml", metrics_path: str = "metrics.json"):
        self.config_path = Path(config_path)
        self.metrics_path = Path(metrics_path)
        self.config: dict = {}
        self.metrics: dict = {}
        self.env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=False,  # HTML output — we control the templates
        )

    # ── Loading ─────────────────────────────────────────────────

    def load_config(self, path: Path | None = None) -> dict:
        """Load and parse the presentation YAML config."""
        p = path or self.config_path
        with open(p, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
        return self.config

    def load_metrics(self, path: Path | None = None) -> dict:
        """Load the metrics JSON data file."""
        p = path or self.metrics_path
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                self.metrics = json.load(f)
        else:
            self.metrics = {}
        return self.metrics

    # ── Data Resolution ─────────────────────────────────────────

    @staticmethod
    def resolve_data(data, metrics: dict):
        """
        Walk a data structure and interpolate {{ metrics.x.y }} references.
        Works on strings, lists, and dicts recursively.
        """
        if isinstance(data, str):
            return PresentationBuilder._interpolate_string(data, metrics)
        elif isinstance(data, list):
            return [PresentationBuilder.resolve_data(item, metrics) for item in data]
        elif isinstance(data, dict):
            return {k: PresentationBuilder.resolve_data(v, metrics) for k, v in data.items()}
        return data

    @staticmethod
    def _interpolate_string(s: str, metrics: dict) -> str:
        """Replace {{ metrics.x.y.z }} patterns with actual values from metrics dict."""
        pattern = r"\{\{\s*metrics\.([a-zA-Z0-9_.]+)\s*\}\}"

        def replacer(match):
            path = match.group(1)
            value = metrics
            for key in path.split("."):
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return match.group(0)  # Leave unreplaced if path doesn't resolve
            return str(value)

        return re.sub(pattern, replacer, s)

    def _find_unresolved(self, data) -> list[str]:
        """Find any remaining {{ metrics.x.y }} patterns in resolved data."""
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

    # ── Validation ─────────────────────────────────────────────

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

    # ── Rendering ───────────────────────────────────────────────

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

        # Page number formatting
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

    def render_navigator(self, slide_files: list[str], slide_titles: list[str],
                         slide_transitions: list[str] | None = None) -> str:
        """Render the present.html navigator shell."""
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

    # ── Theme Generation ───────────────────────────────────────

    def generate_variables_css(self, theme: dict) -> str:
        """
        Generate a custom variables.css from the presentation.yaml theme section.
        Derives accent variants (dim, glow, border, bg) from the hex accent color.
        Falls back to defaults for any missing values.
        """
        primary = theme.get("primary", "#1C2537")
        accent = theme.get("accent", "#C4A962")
        fonts = theme.get("fonts", {})

        # Derive dark variant of primary
        primary_dark = _darken_hex(primary, 0.4)

        # Derive accent RGBA variants
        ar, ag, ab = _hex_to_rgb(accent)

        # Secondary accent
        secondary = theme.get("secondary_accent", "#5B8FA8")
        sr, sg, sb = _hex_to_rgb(secondary)

        # Style presets
        style = theme.get("style", "modern")
        style_overrides = {
            "modern": {"radius_lg": "8px", "shadow": "0 4px 6px rgba(0, 0, 0, 0.2)"},
            "minimal": {"radius_lg": "2px", "shadow": "none"},
            "bold": {"radius_lg": "12px", "shadow": "0 8px 16px rgba(0, 0, 0, 0.3)"},
        }
        preset = style_overrides.get(style, style_overrides["modern"])

        font_heading = fonts.get("heading", "Playfair Display")
        font_subheading = fonts.get("subheading", "Montserrat")
        font_body = fonts.get("body", "Lato")

        # Read the stock variables.css as a base, then replace the :root block
        stock = (THEME_DIR / "variables.css").read_text(encoding="utf-8")

        # Build the custom :root block
        custom_root = f""":root {{
  /* ── Colors (generated from presentation.yaml) ──────────── */
  --pf-primary:       {primary};
  --pf-primary-dark:  {primary_dark};
  --pf-accent:        {accent};
  --pf-accent-dim:    rgba({ar}, {ag}, {ab}, 0.4);
  --pf-accent-glow:   rgba({ar}, {ag}, {ab}, 0.15);
  --pf-accent-border: rgba({ar}, {ag}, {ab}, 0.3);
  --pf-accent-bg:     rgba({ar}, {ag}, {ab}, 0.1);
  --pf-accent-bg-subtle: rgba({ar}, {ag}, {ab}, 0.06);

  --pf-white:         #ffffff;
  --pf-text:          #e0e0e0;
  --pf-text-light:    #cccccc;
  --pf-text-muted:    #aaaaaa;
  --pf-text-dim:      #888888;
  --pf-text-faint:    rgba(255, 255, 255, 0.3);

  --pf-card-bg:       rgba(255, 255, 255, 0.03);
  --pf-card-bg-hover: rgba(255, 255, 255, 0.06);
  --pf-card-border:   rgba({ar}, {ag}, {ab}, 0.2);
  --pf-dark-bg:       rgba(0, 0, 0, 0.2);
  --pf-darker-bg:     rgba(0, 0, 0, 0.25);

  /* Category accent colors */
  --pf-cat-art:       #e74c3c;
  --pf-cat-watches:   #f1c40f;
  --pf-cat-vehicles:  #e67e22;
  --pf-cat-marine:    #3498db;
  --pf-cat-aviation:  #9b59b6;
  --pf-cat-realestate:#2ecc71;

  /* Semantic colors */
  --pf-success:       #2ecc71;
  --pf-danger:        #e74c3c;
  --pf-info:          #3498db;

  /* ── Typography (generated from presentation.yaml) ──────── */
  --pf-font-heading:    '{font_heading}', serif;
  --pf-font-subheading: '{font_subheading}', sans-serif;
  --pf-font-body:       '{font_body}', sans-serif;
  --pf-font-mono:       'IBM Plex Mono', monospace;

  /* ── Secondary Accent (generated) ──────────────────────── */
  --pf-secondary-accent:        {secondary};
  --pf-secondary-accent-dim:    rgba({sr}, {sg}, {sb}, 0.4);
  --pf-secondary-accent-bg:     rgba({sr}, {sg}, {sb}, 0.1);

  /* ── Style Preset: {style} ─────────────────────────────── */
  --pf-radius-lg:     {preset['radius_lg']};
  --pf-shadow-card:   {preset['shadow']};"""

        # Grab everything after the :root color/typography block (spacing, radius, etc.)
        # Find the slide dimensions section onward and append it
        marker = "/* ── Slide Dimensions"
        marker_idx = stock.find(marker)
        if marker_idx != -1:
            # Find start of the line
            line_start = stock.rfind("\n", 0, marker_idx)
            remainder = stock[line_start:]
            custom_root += "\n" + remainder
        else:
            custom_root += "\n}"

        return custom_root

    # ── Full Build ──────────────────────────────────────────────

    def build(self, output_dir: str = "slides") -> Path:
        """
        Full build pipeline:
        1. Load config + metrics
        2. Resolve metrics references in slide data
        3. Render each slide to HTML
        4. Render navigator shell
        5. Copy theme CSS files
        6. Generate custom variables.css from theme config
        7. Write everything to output_dir
        """
        self.load_config()
        self.load_metrics()

        # Validate config
        errors = self.validate_config()
        if errors:
            for e in errors:
                click.echo(click.style(f"  ✗ {e}", fg="red"), err=True)
            raise click.ClickException("Config validation failed. Fix errors above.")

        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        slides = self.config.get("slides", [])
        slide_files = []
        slide_titles = []
        slide_transitions = []

        warnings = []
        for i, slide_cfg in enumerate(slides):
            resolved_data = self.resolve_data(slide_cfg.get("data", {}), self.metrics)
            unresolved = self._find_unresolved(resolved_data)
            for ref in unresolved:
                click.echo(
                    click.style(f"  ⚠ slide {i+1:02d}: ", fg="yellow")
                    + f"unresolved reference {ref}"
                )
            slide_cfg["data"] = resolved_data

            warning = LayoutAnalyzer.analyze_slide(slide_cfg, i)
            if warning:
                warnings.append(warning)

            density = LayoutAnalyzer.compute_density(slide_cfg)

            html = self.render_slide(slide_cfg, i, density=density)

            filename = f"slide_{i + 1:02d}.html"
            (out / filename).write_text(html, encoding="utf-8")

            slide_files.append(filename)
            slide_titles.append(slide_cfg.get("data", {}).get("title", f"Slide {i + 1}"))
            slide_transitions.append(slide_cfg.get("transition", "fade"))

        self._warnings = warnings

        # ── Contrast checks ──────────────────────────────────────
        theme_cfg = self.config.get("theme", {})
        self._contrast_warnings = check_contrast(
            primary=theme_cfg.get("primary", "#1C2537"),
            accent=theme_cfg.get("accent", "#C4A962"),
            secondary_accent=theme_cfg.get("secondary_accent"),
        )
        for cw in self._contrast_warnings:
            click.echo(
                click.style("  ⚠ contrast: ", fg="yellow") + cw
            )

        # Copy local image assets referenced by image layout slides
        for slide_cfg in slides:
            if slide_cfg.get("layout") == "image":
                img_path = Path(slide_cfg.get("data", {}).get("image", ""))
                if img_path.exists() and not img_path.is_absolute():
                    dest = out / img_path
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(img_path, dest)

        # Render and write navigator
        nav_html = self.render_navigator(slide_files, slide_titles, slide_transitions)
        (out / "present.html").write_text(nav_html, encoding="utf-8")

        # Copy theme CSS files (base + components)
        theme_out = out / "theme"
        if theme_out.exists():
            shutil.rmtree(theme_out)
        shutil.copytree(THEME_DIR, theme_out)

        # Generate custom variables.css from presentation.yaml theme
        theme_cfg = self.config.get("theme", {})
        custom_vars = self.generate_variables_css(theme_cfg)
        (theme_out / "variables.css").write_text(custom_vars, encoding="utf-8")

        return out
