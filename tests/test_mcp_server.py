"""Tests for pf.mcp_server tool functions."""

import json
import tempfile
from pathlib import Path

import pytest
import yaml

from pf.mcp_server import (
    build_presentation,
    check_contrast,
    get_layout_example,
    init_presentation,
    list_layouts,
    validate_config,
)


# ── Helpers ──────────────────────────────────────────────────────

def _write_valid_config(tmp_path: Path) -> Path:
    """Write a minimal valid presentation config and return its path."""
    config = {
        "meta": {"title": "Test", "authors": ["Tester"]},
        "theme": {
            "primary": "#1C2537",
            "accent": "#C4A962",
            "fonts": {
                "heading": "Playfair Display",
                "subheading": "Montserrat",
                "body": "Lato",
            },
        },
        "slides": [
            {"layout": "title", "data": {"title": "Hello"}},
            {"layout": "closing", "data": {"title": "Bye"}},
        ],
    }
    config_path = tmp_path / "presentation.yaml"
    config_path.write_text(yaml.dump(config, sort_keys=False), encoding="utf-8")
    metrics_path = tmp_path / "metrics.json"
    metrics_path.write_text(json.dumps({"metadata": {}, "summary": {}}), encoding="utf-8")
    return config_path


# ── build_presentation ───────────────────────────────────────────

class TestBuildPresentation:
    def test_successful_build(self, tmp_path):
        config_path = _write_valid_config(tmp_path)
        out_dir = str(tmp_path / "output")
        result = build_presentation(
            config_path=str(config_path),
            metrics_path=str(tmp_path / "metrics.json"),
            output_dir=out_dir,
        )
        assert "error" not in result
        assert result["slide_count"] == 2
        assert result["output_dir"] == out_dir
        assert isinstance(result["warnings"], list)
        assert isinstance(result["contrast_warnings"], list)

    def test_missing_config_returns_error(self):
        result = build_presentation(config_path="/nonexistent/config.yaml")
        assert "error" in result
        assert "not found" in result["error"]


# ── validate_config ──────────────────────────────────────────────

class TestValidateConfig:
    def test_valid_config_passes(self, tmp_path):
        config_path = _write_valid_config(tmp_path)
        result = validate_config(config_path=str(config_path))
        assert result["valid"] is True
        assert result["errors"] == []

    def test_invalid_config_returns_errors(self, tmp_path):
        config_path = tmp_path / "bad.yaml"
        config_path.write_text(yaml.dump({"slides": "not-a-list"}), encoding="utf-8")
        result = validate_config(config_path=str(config_path))
        assert result["valid"] is False
        assert len(result["errors"]) > 0

    def test_missing_file_returns_error(self):
        result = validate_config(config_path="/nonexistent/config.yaml")
        assert "error" in result
        assert "not found" in result["error"]


# ── check_contrast ───────────────────────────────────────────────

class TestCheckContrast:
    def test_good_contrast_passes(self):
        # Gold accent on dark background — high contrast, distinct from text
        result = check_contrast(primary="#1C2537", accent="#C4A962")
        assert result["passes"] is True
        assert result["warnings"] == []
        assert result["ratios"]["accent_on_primary"] >= 3.0

    def test_bad_contrast_warns(self):
        # Dark gray accent on dark background — low contrast
        result = check_contrast(primary="#1C2537", accent="#2a3040")
        assert result["passes"] is False
        assert len(result["warnings"]) > 0

    def test_secondary_accent_in_ratios(self):
        result = check_contrast(
            primary="#000000", accent="#ffffff", secondary_accent="#5B8FA8"
        )
        assert "secondary_on_primary" in result["ratios"]


# ── list_layouts ─────────────────────────────────────────────────

class TestListLayouts:
    def test_returns_all_layouts(self):
        layouts = list_layouts()
        assert len(layouts) == 11

    def test_each_has_name_and_description(self):
        layouts = list_layouts()
        for layout in layouts:
            assert "name" in layout
            assert "description" in layout
            assert isinstance(layout["name"], str)
            assert isinstance(layout["description"], str)


# ── init_presentation ────────────────────────────────────────────

class TestInitPresentation:
    def test_scaffolds_project(self, tmp_path):
        result = init_presentation(name="my-deck", directory=str(tmp_path))
        assert "error" not in result
        project_dir = Path(result["project_dir"])
        assert (project_dir / "presentation.yaml").exists()
        assert (project_dir / "metrics.json").exists()
        assert (project_dir / "slides").is_dir()

    def test_existing_dir_returns_error(self, tmp_path):
        (tmp_path / "existing").mkdir()
        result = init_presentation(name="existing", directory=str(tmp_path))
        assert "error" in result
        assert "already exists" in result["error"]


# ── get_layout_example ──────────────────────────────────────────

class TestGetLayoutExample:
    def test_get_layout_example_returns_yaml_for_known_layout(self):
        """get_layout_example should return YAML example + description for a valid layout."""
        result = get_layout_example("title")
        assert "error" not in result
        assert "name" in result
        assert result["name"] == "title"
        assert "description" in result
        assert "yaml_example" in result
        assert "layout: title" in result["yaml_example"]
        assert "data:" in result["yaml_example"]

    def test_get_layout_example_returns_error_for_unknown_layout(self):
        """get_layout_example should return an error for an invalid layout name."""
        result = get_layout_example("nonexistent")
        assert "error" in result

    def test_get_layout_example_all_layouts_have_examples(self):
        """Every layout in list_layouts should have a corresponding example."""
        layouts = list_layouts()
        for layout in layouts:
            result = get_layout_example(layout["name"])
            assert "error" not in result, f"Missing example for layout: {layout['name']}"
            assert "yaml_example" in result
