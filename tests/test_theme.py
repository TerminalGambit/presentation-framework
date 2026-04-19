"""Tests for expanded theme options."""
import json
import tempfile
from pathlib import Path

import click
import pytest
import yaml

from pf import builder as builder_mod
from pf.builder import PresentationBuilder, _deep_merge


@pytest.fixture
def preset_dir(tmp_path, monkeypatch):
    """Point PRESETS_DIR at a tmpdir so tests don't depend on the real preset registry."""
    presets = tmp_path / "presets"
    presets.mkdir()
    monkeypatch.setattr(builder_mod, "PRESETS_DIR", presets)
    return presets


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


class TestContrastWarnings:
    def test_build_emits_contrast_warning_for_bad_colors(self):
        """Build should warn when accent is too close to primary."""
        with tempfile.TemporaryDirectory() as tmp:
            config = {
                "meta": {"title": "Contrast Test"},
                "theme": {
                    "primary": "#1C2537",
                    "accent": "#1A2030",  # Nearly identical to primary
                    "fonts": {"heading": "Playfair Display", "subheading": "Montserrat", "body": "Lato"},
                },
                "slides": [{"layout": "closing", "data": {"title": "Test"}}],
            }
            config_path = Path(tmp) / "presentation.yaml"
            config_path.write_text(yaml.dump(config), encoding="utf-8")
            metrics_path = Path(tmp) / "metrics.json"
            metrics_path.write_text(json.dumps({}), encoding="utf-8")

            builder = PresentationBuilder(
                config_path=str(config_path), metrics_path=str(metrics_path)
            )
            builder.build(output_dir=str(Path(tmp) / "slides"))
            assert len(builder._contrast_warnings) > 0

    def test_build_no_contrast_warning_for_good_colors(self):
        """Default colors should not trigger contrast warnings."""
        with tempfile.TemporaryDirectory() as tmp:
            config = {
                "meta": {"title": "Good Contrast"},
                "theme": {
                    "primary": "#1C2537",
                    "accent": "#C4A962",
                    "fonts": {"heading": "Playfair Display", "subheading": "Montserrat", "body": "Lato"},
                },
                "slides": [{"layout": "closing", "data": {"title": "Test"}}],
            }
            config_path = Path(tmp) / "presentation.yaml"
            config_path.write_text(yaml.dump(config), encoding="utf-8")
            metrics_path = Path(tmp) / "metrics.json"
            metrics_path.write_text(json.dumps({}), encoding="utf-8")

            builder = PresentationBuilder(
                config_path=str(config_path), metrics_path=str(metrics_path)
            )
            builder.build(output_dir=str(Path(tmp) / "slides"))
            assert len(builder._contrast_warnings) == 0


class TestDeepMerge:
    """Unit tests for the preset/override merge helper."""

    def test_scalars_in_override_win(self):
        merged = _deep_merge({"a": 1, "b": 2}, {"b": 99})
        assert merged == {"a": 1, "b": 99}

    def test_dict_keys_recurse(self):
        base = {"fonts": {"heading": "Serif", "body": "Sans"}}
        override = {"fonts": {"heading": "Mono"}}
        merged = _deep_merge(base, override)
        assert merged == {"fonts": {"heading": "Mono", "body": "Sans"}}

    def test_dict_replaces_scalar(self):
        merged = _deep_merge({"x": 1}, {"x": {"nested": True}})
        assert merged == {"x": {"nested": True}}

    def test_does_not_mutate_inputs(self):
        base = {"fonts": {"heading": "Serif"}}
        override = {"fonts": {"heading": "Mono"}}
        _deep_merge(base, override)
        assert base == {"fonts": {"heading": "Serif"}}
        assert override == {"fonts": {"heading": "Mono"}}


class TestThemePreset:
    """T1.1 — theme.preset key + precedence rule."""

    def test_preset_alone_loads_tokens(self, preset_dir):
        (preset_dir / "demo.yaml").write_text(yaml.dump({
            "primary": "#001122",
            "accent": "#FFAA00",
            "secondary_accent": "#00AAFF",
            "fonts": {"heading": "Inter", "subheading": "Inter", "body": "Inter"},
            "style": "minimal",
        }))
        b = PresentationBuilder()
        css = b.generate_variables_css({"preset": "demo"})
        assert "#001122" in css
        assert "#FFAA00" in css
        assert "Inter" in css

    def test_preset_with_user_overrides(self, preset_dir):
        """User scalar keys win; user dict keys merge into preset dict keys."""
        (preset_dir / "demo.yaml").write_text(yaml.dump({
            "primary": "#001122",
            "accent": "#FFAA00",
            "fonts": {"heading": "Inter", "subheading": "Inter", "body": "Inter"},
        }))
        b = PresentationBuilder()
        css = b.generate_variables_css({
            "preset": "demo",
            "accent": "#FF0000",  # user override wins
            "fonts": {"heading": "Roboto"},  # merges into preset fonts
        })
        assert "#FF0000" in css
        assert "#001122" in css  # preset primary preserved
        assert "Roboto" in css  # user heading wins
        assert "Inter" in css  # subheading/body still from preset

    def test_unknown_preset_raises_with_available_list(self, preset_dir):
        (preset_dir / "alpha.yaml").write_text(yaml.dump({"primary": "#000000", "accent": "#ffffff"}))
        b = PresentationBuilder()
        with pytest.raises(click.ClickException) as exc:
            b.generate_variables_css({"preset": "missing"})
        assert "missing" in str(exc.value.message)
        assert "alpha" in str(exc.value.message)

    def test_no_preset_unchanged(self):
        """Without preset key: identical output to pre-T1.1 code path."""
        b = PresentationBuilder()
        css_no_preset = b.generate_variables_css({
            "primary": "#1C2537",
            "accent": "#C4A962",
            "fonts": {"heading": "Playfair Display", "subheading": "Montserrat", "body": "Lato"},
        })
        # The hard-coded fallback path still uses these defaults — sanity-check that
        # the absence of `preset` does NOT trigger preset loading (no exception even
        # if PRESETS_DIR doesn't exist on the system).
        assert "#1C2537" in css_no_preset
        assert "Playfair Display" in css_no_preset
        # Without preset, nothing from a preset dir gets read
        assert "Inter" not in css_no_preset
