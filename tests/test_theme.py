"""Tests for expanded theme options."""
import json
import tempfile
from pathlib import Path

import yaml

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


class TestMathSupport:
    def test_math_enabled_loads_katex(self):
        """When theme.math is true, base template should include KaTeX CDN links."""
        with tempfile.TemporaryDirectory() as tmp:
            config = {
                "meta": {"title": "Math Test"},
                "theme": {"primary": "#1C2537", "accent": "#C4A962", "math": True, "fonts": {"heading": "Playfair Display", "subheading": "Montserrat", "body": "Lato"}},
                "slides": [{"layout": "closing", "data": {"title": "Test"}}],
            }
            config_path = Path(tmp) / "presentation.yaml"
            config_path.write_text(yaml.dump(config), encoding="utf-8")
            metrics_path = Path(tmp) / "metrics.json"
            metrics_path.write_text(json.dumps({}), encoding="utf-8")

            builder = PresentationBuilder(
                config_path=str(config_path), metrics_path=str(metrics_path)
            )
            out = builder.build(output_dir=str(Path(tmp) / "slides"))

            slide_html = (out / "slide_01.html").read_text(encoding="utf-8")
            assert "katex.min.css" in slide_html
            assert "katex.min.js" in slide_html
            assert "auto-render.min.js" in slide_html

    def test_math_disabled_no_katex(self):
        """When theme.math is absent/false, no KaTeX should be loaded."""
        with tempfile.TemporaryDirectory() as tmp:
            config = {
                "meta": {"title": "No Math"},
                "theme": {"primary": "#1C2537", "accent": "#C4A962", "fonts": {"heading": "Playfair Display", "subheading": "Montserrat", "body": "Lato"}},
                "slides": [{"layout": "closing", "data": {"title": "Test"}}],
            }
            config_path = Path(tmp) / "presentation.yaml"
            config_path.write_text(yaml.dump(config), encoding="utf-8")
            metrics_path = Path(tmp) / "metrics.json"
            metrics_path.write_text(json.dumps({}), encoding="utf-8")

            builder = PresentationBuilder(
                config_path=str(config_path), metrics_path=str(metrics_path)
            )
            out = builder.build(output_dir=str(Path(tmp) / "slides"))

            slide_html = (out / "slide_01.html").read_text(encoding="utf-8")
            assert "katex" not in slide_html

    def test_math_in_slide_content(self):
        """Math delimiters in slide text should pass through to HTML unchanged."""
        with tempfile.TemporaryDirectory() as tmp:
            config = {
                "meta": {"title": "Math"},
                "theme": {"primary": "#1C2537", "accent": "#C4A962", "math": True,
                          "fonts": {"heading": "Playfair Display", "subheading": "Montserrat", "body": "Lato"}},
                "slides": [{
                    "layout": "closing",
                    "data": {
                        "title": "Euler's Identity",
                        "subtitle": "$e^{i\\pi} + 1 = 0$",
                    },
                }],
            }
            config_path = Path(tmp) / "presentation.yaml"
            config_path.write_text(yaml.dump(config), encoding="utf-8")
            metrics_path = Path(tmp) / "metrics.json"
            metrics_path.write_text(json.dumps({}), encoding="utf-8")

            builder = PresentationBuilder(
                config_path=str(config_path), metrics_path=str(metrics_path)
            )
            out = builder.build(output_dir=str(Path(tmp) / "slides"))

            slide_html = (out / "slide_01.html").read_text(encoding="utf-8")
            # Math delimiters should pass through to HTML for KaTeX auto-render
            assert "$e^{i\\pi} + 1 = 0$" in slide_html
            # KaTeX should be loaded
            assert "katex.min.js" in slide_html
