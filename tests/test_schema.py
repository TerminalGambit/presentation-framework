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
