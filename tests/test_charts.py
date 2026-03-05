"""Tests for interactive chart support (Plotly.js)."""

import pytest
import json
import yaml
from pathlib import Path


class TestChartSchema:
    def test_charts_theme_option_valid(self):
        from pf.builder import PresentationBuilder
        b = PresentationBuilder()
        b.config = {
            "meta": {"title": "Test"},
            "theme": {"primary": "#1C2537", "accent": "#C4A962", "charts": True},
            "slides": [{"layout": "title", "data": {"title": "Hi"}}],
        }
        errors = b.validate_config()
        assert errors == []

    def test_chart_layout_in_schema(self):
        from pf.builder import PresentationBuilder
        b = PresentationBuilder()
        b.config = {
            "meta": {"title": "Test"},
            "theme": {"primary": "#1C2537", "accent": "#C4A962"},
            "slides": [{"layout": "chart", "data": {"title": "Revenue", "chart_type": "bar"}}],
        }
        errors = b.validate_config()
        assert errors == []


class TestChartCDN:
    def _build_slide(self, tmp_path, theme_cfg, slides):
        from pf.builder import PresentationBuilder
        config_path = tmp_path / "presentation.yaml"
        config = {
            "meta": {"title": "Test"},
            "theme": theme_cfg,
            "slides": slides,
        }
        config_path.write_text(yaml.dump(config, sort_keys=False), encoding="utf-8")
        metrics_path = tmp_path / "metrics.json"
        metrics_path.write_text(json.dumps({}), encoding="utf-8")
        builder = PresentationBuilder(config_path=str(config_path), metrics_path=str(metrics_path))
        import contextlib, io
        with contextlib.redirect_stdout(io.StringIO()):
            out = builder.build(output_dir=str(tmp_path / "slides"))
        return Path(out)

    def test_charts_enabled_loads_plotly(self, tmp_path):
        slides_dir = self._build_slide(tmp_path,
            {"primary": "#1C2537", "accent": "#C4A962", "charts": True,
             "fonts": {"heading": "Playfair Display", "subheading": "Montserrat", "body": "Lato"}},
            [{"layout": "title", "data": {"title": "Hi"}}])
        html = (slides_dir / "slide_01.html").read_text()
        assert "plotly" in html.lower()
        assert "initChart" in html

    def test_charts_disabled_no_plotly(self, tmp_path):
        slides_dir = self._build_slide(tmp_path,
            {"primary": "#1C2537", "accent": "#C4A962",
             "fonts": {"heading": "Playfair Display", "subheading": "Montserrat", "body": "Lato"}},
            [{"layout": "title", "data": {"title": "Hi"}}])
        html = (slides_dir / "slide_01.html").read_text()
        assert "plotly" not in html.lower()
