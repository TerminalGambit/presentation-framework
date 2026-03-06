"""Tests for pf.mcp_server tool functions."""

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from pf.mcp_server import (
    build_presentation,
    check_accessibility_output,
    check_contrast,
    generate_presentation,
    get_layout_example,
    get_layout_schema,
    init_presentation,
    list_layouts,
    optimize_slide,
    suggest_layout,
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


# ── generate_presentation ────────────────────────────────────────

class TestGeneratePresentation:
    def test_generate_requires_llm_extra_when_instructor_missing(self):
        """When instructor is not installed, return error with install instructions."""
        # Simulate instructor being unavailable by patching sys.modules
        original = sys.modules.get("instructor", _SENTINEL := object())
        sys.modules["instructor"] = None  # type: ignore[assignment]
        try:
            result = generate_presentation(prompt="test presentation")
        finally:
            # Restore original state
            if original is _SENTINEL:
                sys.modules.pop("instructor", None)
            else:
                sys.modules["instructor"] = original  # type: ignore[assignment]

        assert isinstance(result, dict)
        assert "error" in result
        # Error message should mention how to install
        error_msg = result["error"].lower()
        assert "pip install" in error_msg or "pf[llm]" in error_msg

    def test_generate_returns_dict(self):
        """generate_presentation must always return a dict."""
        result = generate_presentation(prompt="test about AI")
        assert isinstance(result, dict)
        # Either a success payload or a graceful error
        if "error" in result:
            assert isinstance(result["error"], str)
        else:
            assert "yaml_config" in result
            assert "metrics" in result

    def test_generate_with_mocked_instructor(self):
        """With a mocked instructor client, generate_presentation returns sanitized output."""
        import yaml as _yaml

        from pf.llm_schemas import PresentationOutput

        # Build a minimal PresentationOutput that our mock will return
        fake_yaml = _yaml.dump({
            "meta": {"title": "AI Trends"},
            "theme": {"primary": "#1E293B", "accent": "#6366F1"},
            "slides": [
                {"layout": "title", "data": {"title": "AI Trends 2026"}},
                {"layout": "section", "data": {"title": "<script>xss</script>Safe Section"}},
                {"layout": "closing", "data": {"title": "Thank You"}},
            ],
        }, default_flow_style=False, sort_keys=False)
        fake_output = PresentationOutput(yaml_config=fake_yaml, metrics={"count": 3})

        mock_client = MagicMock()
        mock_client.create.return_value = fake_output

        mock_instructor = MagicMock()
        mock_instructor.from_provider.return_value = mock_client
        mock_instructor.Mode.TOOLS = "tools"

        with patch.dict("sys.modules", {"instructor": mock_instructor}):
            result = generate_presentation(prompt="AI trends", style="modern", length="short")

        assert "error" not in result, f"Unexpected error: {result.get('error')}"
        assert "yaml_config" in result
        assert "metrics" in result

        # Verify the XSS content was stripped from the sanitized output
        assert "script" not in result["yaml_config"].lower()
        assert "Safe Section" in result["yaml_config"]

        # Metrics passthrough
        assert result["metrics"]["count"] == 3

    def test_generate_sanitizes_metrics(self):
        """generate_presentation must sanitize the metrics dict too."""
        import yaml as _yaml

        from pf.llm_schemas import PresentationOutput

        fake_yaml = _yaml.dump({
            "meta": {"title": "Test"},
            "theme": {},
            "slides": [{"layout": "title", "data": {"title": "Test"}}],
        }, default_flow_style=False, sort_keys=False)
        fake_output = PresentationOutput(
            yaml_config=fake_yaml,
            metrics={"label": "<script>evil</script>Clean"},
        )

        mock_client = MagicMock()
        mock_client.create.return_value = fake_output
        mock_instructor = MagicMock()
        mock_instructor.from_provider.return_value = mock_client
        mock_instructor.Mode.TOOLS = "tools"

        with patch.dict("sys.modules", {"instructor": mock_instructor}):
            result = generate_presentation(prompt="test")

        assert "script" not in str(result["metrics"]).lower()
        assert "Clean" in result["metrics"]["label"]

    def test_generate_handles_llm_exception(self):
        """If the LLM call raises, generate_presentation returns error dict."""
        mock_client = MagicMock()
        mock_client.create.side_effect = RuntimeError("API timeout")

        mock_instructor = MagicMock()
        mock_instructor.from_provider.return_value = mock_client
        mock_instructor.Mode.TOOLS = "tools"

        with patch.dict("sys.modules", {"instructor": mock_instructor}):
            result = generate_presentation(prompt="test")

        assert "error" in result
        assert "API timeout" in result["error"]


# ── get_layout_schema ────────────────────────────────────────────

class TestGetLayoutSchema:
    def test_get_schema_returns_json_schema(self):
        """get_layout_schema should return a dict with 'properties' for a known layout."""
        result = get_layout_schema("timeline")
        assert isinstance(result, dict)
        assert "properties" in result

    def test_get_schema_unknown_layout(self):
        """get_layout_schema should return error dict for an unknown layout."""
        result = get_layout_schema("nonexistent")
        assert "error" in result
        assert "nonexistent" in result["error"]

    def test_get_schema_has_constraints(self):
        """two-column schema should include maxItems constraints for list fields."""
        result = get_layout_schema("two-column")
        schema_str = json.dumps(result)
        assert "maxItems" in schema_str

    def test_get_schema_all_layouts_return_valid_schema(self):
        """Every core layout name should return a schema with 'properties'."""
        core_layouts = [
            "title", "two-column", "three-column", "data-table", "stat-grid",
            "chart", "closing", "image", "section", "quote", "timeline",
        ]
        for name in core_layouts:
            result = get_layout_schema(name)
            assert "error" not in result, f"Unexpected error for layout {name!r}: {result}"
            assert "properties" in result, f"No 'properties' in schema for {name!r}"

    def test_get_schema_timeline_has_steps(self):
        """timeline schema should include a 'steps' property."""
        result = get_layout_schema("timeline")
        assert "steps" in result["properties"]

    def test_get_schema_title_field_is_required(self):
        """Most layout schemas should list 'title' in required fields (if applicable)."""
        result = get_layout_schema("section")
        # 'title' is a required field in SectionSlide
        assert "title" in result.get("required", []) or "title" in result.get("properties", {})


# ── optimize_slide ────────────────────────────────────────────────

class TestOptimizeSlide:
    def test_optimize_non_overflowing_slide(self):
        """A simple title slide should not be split."""
        slide = {"layout": "title", "data": {"title": "Hello World"}}
        result = optimize_slide(yaml.dump(slide))
        assert "error" not in result
        assert "slides" in result
        assert result["count"] == 1
        assert result["was_split"] is False

    def test_optimize_overflowing_two_column(self):
        """A two-column slide with 8 cards per column (3 bullets each) should be split."""
        cards = [
            {
                "type": "card",
                "title": f"Card {i}",
                "bullets": [f"Bullet {j} of card {i}" for j in range(3)],
            }
            for i in range(8)
        ]
        slide = {
            "layout": "two-column",
            "data": {
                "title": "Overflowing Slide",
                "left": cards,
                "right": cards,
            },
        }
        result = optimize_slide(yaml.dump(slide))
        assert "error" not in result
        assert result["was_split"] is True
        assert result["count"] >= 2

    def test_optimize_invalid_yaml(self):
        """Invalid YAML input should return an error dict."""
        result = optimize_slide("{{{{not yaml")
        assert "error" in result
        assert isinstance(result["error"], str)


# ── suggest_layout ────────────────────────────────────────────────

class TestSuggestLayout:
    def test_suggest_requires_llm_extra_when_instructor_missing(self):
        """When instructor is not installed, return error with install instructions."""
        original = sys.modules.get("instructor", _SENTINEL := object())
        sys.modules["instructor"] = None  # type: ignore[assignment]
        try:
            result = suggest_layout(slides_yaml="- layout: title\n  data:\n    title: Test\n")
        finally:
            if original is _SENTINEL:
                sys.modules.pop("instructor", None)
            else:
                sys.modules["instructor"] = original  # type: ignore[assignment]

        assert isinstance(result, dict)
        assert "error" in result
        error_msg = result["error"].lower()
        assert "pip install" in error_msg or "pf[llm]" in error_msg

    def test_suggest_returns_dict(self):
        """suggest_layout must always return a dict."""
        result = suggest_layout(
            slides_yaml="- layout: title\n  data:\n    title: Test\n",
            topic="AI trends",
        )
        assert isinstance(result, dict)
        # Either a success payload or a graceful error
        if "error" in result:
            assert isinstance(result["error"], str)
        else:
            assert "suggestions" in result


# ── check_accessibility_output ────────────────────────────────────

class TestCheckAccessibilityOutput:
    def test_check_accessibility_clean_output(self, tmp_path):
        """An HTML slide with proper alt and aria-label should pass."""
        slide_html = (
            '<!DOCTYPE html><html><body>'
            '<div class="slide-container" role="region" aria-label="Slide 1" tabindex="0">'
            '<img src="photo.jpg" alt="Team Photo">'
            '<button aria-label="Next slide">Next</button>'
            '</div></body></html>'
        )
        slide_file = tmp_path / "slide_01.html"
        slide_file.write_text(slide_html, encoding="utf-8")

        result = check_accessibility_output(str(tmp_path))
        assert "error" not in result
        assert result["pass"] is True
        assert result["warning_count"] == 0
        assert isinstance(result["warnings"], list)

    def test_check_accessibility_missing_alt(self, tmp_path):
        """An HTML slide with a missing alt attribute should fail with a warning."""
        slide_html = (
            '<!DOCTYPE html><html><body>'
            '<div class="slide-container" role="region" aria-label="Slide 1" tabindex="0">'
            '<img src="photo.jpg">'  # no alt attribute
            '</div></body></html>'
        )
        slide_file = tmp_path / "slide_01.html"
        slide_file.write_text(slide_html, encoding="utf-8")

        result = check_accessibility_output(str(tmp_path))
        assert "error" not in result
        assert result["pass"] is False
        assert result["warning_count"] >= 1
        # At least one warning should mention alt
        assert any("alt" in w["issue"] for w in result["warnings"])
        # Warning dicts should have the expected keys
        for w in result["warnings"]:
            assert "file" in w
            assert "element" in w
            assert "issue" in w
            assert "suggestion" in w
            assert "severity" in w

    def test_check_accessibility_invalid_dir(self):
        """A non-existent directory should return an error dict."""
        result = check_accessibility_output("/nonexistent/path/to/slides")
        assert "error" in result
        assert isinstance(result["error"], str)
