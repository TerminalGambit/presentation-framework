"""Tests for pf.builder.PresentationBuilder."""

import json
import tempfile
from pathlib import Path

import click
import pytest
import yaml

from pf.builder import PresentationBuilder


# ── resolve_data tests ──────────────────────────────────────────

class TestResolveData:
    def test_simple_string_interpolation(self):
        metrics = {"summary": {"total_assets": 128}}
        result = PresentationBuilder.resolve_data(
            "We have {{ metrics.summary.total_assets }} assets", metrics
        )
        assert result == "We have 128 assets"

    def test_nested_dict_interpolation(self):
        metrics = {"summary": {"categories": 9, "total_assets": 128}}
        data = {
            "title": "{{ metrics.summary.total_assets }} Assets",
            "sub": "Across {{ metrics.summary.categories }} categories",
        }
        result = PresentationBuilder.resolve_data(data, metrics)
        assert result["title"] == "128 Assets"
        assert result["sub"] == "Across 9 categories"

    def test_list_interpolation(self):
        metrics = {"summary": {"total_twitter_accounts": 36}}
        data = ["{{ metrics.summary.total_twitter_accounts }} accounts", "static text"]
        result = PresentationBuilder.resolve_data(data, metrics)
        assert result == ["36 accounts", "static text"]

    def test_missing_key_left_unreplaced(self):
        metrics = {"summary": {}}
        result = PresentationBuilder.resolve_data(
            "{{ metrics.summary.nonexistent }}", metrics
        )
        assert result == "{{ metrics.summary.nonexistent }}"

    def test_non_string_passthrough(self):
        assert PresentationBuilder.resolve_data(42, {}) == 42
        assert PresentationBuilder.resolve_data(True, {}) is True
        assert PresentationBuilder.resolve_data(None, {}) is None

    def test_deep_nested_metrics(self):
        metrics = {"breakdown": {"twitter_accounts_by_category": {"Art": 6}}}
        result = PresentationBuilder.resolve_data(
            "{{ metrics.breakdown.twitter_accounts_by_category.Art }}", metrics
        )
        assert result == "6"


# ── render_slide tests ──────────────────────────────────────────

class TestRenderSlide:
    @pytest.fixture
    def builder(self):
        b = PresentationBuilder()
        b.config = {
            "meta": {"title": "Test Deck"},
            "theme": {"fonts": {"heading": "Playfair Display", "subheading": "Montserrat", "body": "Lato"}},
        }
        return b

    def test_render_title_slide(self, builder):
        slide = {
            "layout": "title",
            "data": {
                "title": "Hello World",
                "subtitle": "A Test",
                "tagline": "Testing the framework",
            },
        }
        html = builder.render_slide(slide, 0)
        assert "Hello World" in html
        assert "A Test" in html
        assert "<!DOCTYPE html>" in html

    def test_render_closing_slide(self, builder):
        slide = {
            "layout": "closing",
            "data": {
                "title": "Thank You",
                "subtitle": "Questions",
            },
        }
        html = builder.render_slide(slide, 0)
        assert "Thank You" in html
        assert "Questions" in html

    def test_render_two_column_slide(self, builder):
        slide = {
            "layout": "two-column",
            "data": {
                "title": "Problem",
                "subtitle": "A challenge",
                "left": [{"type": "html", "content": "<p>Left content</p>"}],
                "right": [{"type": "html", "content": "<p>Right content</p>"}],
            },
        }
        html = builder.render_slide(slide, 0)
        assert "Problem" in html
        assert "Left content" in html
        assert "Right content" in html


# ── full build test ─────────────────────────────────────────────

class TestBuild:
    def test_build_creates_output_structure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create minimal presentation.yaml
            config = {
                "meta": {"title": "Test"},
                "theme": {"fonts": {"heading": "Playfair Display", "subheading": "Montserrat", "body": "Lato"}},
                "slides": [
                    {"layout": "title", "data": {"title": "Hello"}},
                    {"layout": "closing", "data": {"title": "Bye"}},
                ],
            }
            config_path = tmpdir / "presentation.yaml"
            config_path.write_text(yaml.dump(config), encoding="utf-8")

            # Create empty metrics.json
            metrics_path = tmpdir / "metrics.json"
            metrics_path.write_text("{}", encoding="utf-8")

            # Build
            builder = PresentationBuilder(
                config_path=str(config_path),
                metrics_path=str(metrics_path),
            )
            out = builder.build(output_dir=str(tmpdir / "slides"))

            # Verify structure
            assert (out / "present.html").exists()
            assert (out / "slide_01.html").exists()
            assert (out / "slide_02.html").exists()
            assert (out / "theme" / "variables.css").exists()
            assert (out / "theme" / "base.css").exists()
            assert (out / "theme" / "components.css").exists()

            # Verify navigator has correct slide references
            nav_html = (out / "present.html").read_text()
            assert "slide_01.html" in nav_html
            assert "slide_02.html" in nav_html

    def test_build_with_metrics_interpolation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            config = {
                "meta": {"title": "Test"},
                "theme": {"fonts": {"heading": "Playfair Display", "subheading": "Montserrat", "body": "Lato"}},
                "slides": [
                    {
                        "layout": "title",
                        "data": {
                            "title": "{{ metrics.summary.total_assets }} Assets",
                        },
                    },
                ],
            }
            (tmpdir / "presentation.yaml").write_text(yaml.dump(config), encoding="utf-8")
            (tmpdir / "metrics.json").write_text(
                json.dumps({"summary": {"total_assets": 128}}), encoding="utf-8"
            )

            builder = PresentationBuilder(
                config_path=str(tmpdir / "presentation.yaml"),
                metrics_path=str(tmpdir / "metrics.json"),
            )
            out = builder.build(output_dir=str(tmpdir / "slides"))

            slide_html = (out / "slide_01.html").read_text()
            assert "128 Assets" in slide_html


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
