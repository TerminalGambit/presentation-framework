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


class TestChartLayout:
    def _build_chart_slide(self, tmp_path, slide_data, metrics=None):
        from pf.builder import PresentationBuilder
        config = {
            "meta": {"title": "Test"},
            "theme": {"primary": "#1C2537", "accent": "#C4A962", "charts": True,
                      "fonts": {"heading": "Playfair Display", "subheading": "Montserrat", "body": "Lato"}},
            "slides": [{"layout": "chart", "data": slide_data}],
        }
        config_path = tmp_path / "presentation.yaml"
        config_path.write_text(yaml.dump(config, sort_keys=False), encoding="utf-8")
        metrics_path = tmp_path / "metrics.json"
        metrics_path.write_text(json.dumps(metrics or {}), encoding="utf-8")
        builder = PresentationBuilder(config_path=str(config_path), metrics_path=str(metrics_path))
        import contextlib, io
        with contextlib.redirect_stdout(io.StringIO()):
            out = builder.build(output_dir=str(tmp_path / "slides"))
        return (Path(out) / "slide_01.html").read_text()

    def test_chart_slide_renders(self, tmp_path):
        html = self._build_chart_slide(tmp_path, {
            "title": "Revenue Growth",
            "chart_type": "bar",
            "labels": ["Q1", "Q2", "Q3"],
            "values": [100, 200, 300],
        })
        assert "Revenue Growth" in html
        assert "chart-container" in html
        assert "initChart" in html

    def test_chart_slide_with_metrics_source(self, tmp_path):
        html = self._build_chart_slide(tmp_path,
            {"title": "Revenue", "chart_type": "line", "source": "{{ metrics.charts.revenue }}"},
            metrics={"charts": {"revenue": {"x": ["Q1", "Q2"], "y": [100, 200]}}})
        assert "Revenue" in html
        assert "Q1" in html

    def test_chart_slide_subtitle(self, tmp_path):
        html = self._build_chart_slide(tmp_path, {
            "title": "Growth", "subtitle": "Year over Year",
            "chart_type": "bar", "labels": ["A"], "values": [1],
        })
        assert "Year over Year" in html
        assert "chart-subtitle" in html

    def test_chart_stores_config_for_modal(self, tmp_path):
        html = self._build_chart_slide(tmp_path, {
            "title": "Test", "chart_type": "pie",
            "labels": ["A", "B"], "values": [60, 40],
        })
        assert 'data-chart-type="pie"' in html
        assert "data-chart-config" in html


class TestChartComponent:
    def _build_two_col(self, tmp_path, left_items, right_items, metrics=None):
        from pf.builder import PresentationBuilder
        config = {
            "meta": {"title": "Test"},
            "theme": {"primary": "#1C2537", "accent": "#C4A962", "charts": True,
                      "fonts": {"heading": "Playfair Display", "subheading": "Montserrat", "body": "Lato"}},
            "slides": [{"layout": "two-column", "data": {
                "header": {"title": "Test"},
                "left": left_items,
                "right": right_items,
            }}],
        }
        config_path = tmp_path / "presentation.yaml"
        config_path.write_text(yaml.dump(config, sort_keys=False), encoding="utf-8")
        metrics_path = tmp_path / "metrics.json"
        metrics_path.write_text(json.dumps(metrics or {}), encoding="utf-8")
        builder = PresentationBuilder(config_path=str(config_path), metrics_path=str(metrics_path))
        import contextlib, io
        with contextlib.redirect_stdout(io.StringIO()):
            out = builder.build(output_dir=str(tmp_path / "slides"))
        return (Path(out) / "slide_01.html").read_text()

    def test_chart_in_two_column_left(self, tmp_path):
        html = self._build_two_col(tmp_path,
            left_items=[{"type": "plotly-chart", "chart_type": "bar", "labels": ["A", "B"], "values": [10, 20]}],
            right_items=[{"type": "html", "content": "<p>Text</p>"}])
        assert "chart-inline" in html
        assert "initChart" in html

    def test_chart_in_two_column_right(self, tmp_path):
        html = self._build_two_col(tmp_path,
            left_items=[{"type": "html", "content": "<p>Text</p>"}],
            right_items=[{"type": "plotly-chart", "chart_type": "line", "labels": ["X", "Y"], "values": [5, 15]}])
        assert "chart-inline" in html


class TestChartModal:
    def test_chart_modal_markup_exists(self):
        template_path = Path(__file__).parent.parent / "templates" / "present.html.j2"
        html = template_path.read_text()
        assert "chartModalOverlay" in html
        assert "chartModalContainer" in html

    def test_chart_modal_js_functions(self):
        template_path = Path(__file__).parent.parent / "templates" / "present.html.j2"
        html = template_path.read_text()
        assert "openChartModal" in html
        assert "closeChartModal" in html

    def test_chart_modal_keyboard_escape(self):
        template_path = Path(__file__).parent.parent / "templates" / "present.html.j2"
        html = template_path.read_text()
        assert "chartModalActive" in html
