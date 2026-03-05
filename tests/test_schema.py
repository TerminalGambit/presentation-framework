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


class TestMathSchema:
    def test_math_theme_option_valid(self):
        """theme.math: true should pass schema validation."""
        import tempfile, json, yaml
        from pathlib import Path
        from pf.builder import PresentationBuilder

        with tempfile.TemporaryDirectory() as tmp:
            config = {
                "theme": {"primary": "#000", "accent": "#fff", "math": True},
                "slides": [{"layout": "closing", "data": {"title": "X"}}],
            }
            config_path = Path(tmp) / "presentation.yaml"
            config_path.write_text(yaml.dump(config), encoding="utf-8")
            metrics_path = Path(tmp) / "metrics.json"
            metrics_path.write_text(json.dumps({}), encoding="utf-8")

            builder = PresentationBuilder(str(config_path), str(metrics_path))
            builder.load_config()
            errors = builder.validate_config()
            assert not errors, f"Unexpected validation errors: {errors}"
