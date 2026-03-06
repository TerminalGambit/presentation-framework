"""Smoke test for the multi-agent presentation workflow (LLM-04).

Verifies that the documented 5-step multi-agent workflow tools can be called
in sequence without crashing. Does NOT require live LLM credentials — all
LLM-dependent tools are exercised only for their graceful error paths.
"""

import json
from pathlib import Path

import pytest
import yaml

from pf.mcp_server import (
    MULTI_AGENT_WORKFLOW,
    build_presentation,
    check_accessibility_output,
    get_layout_example,
    list_layouts,
    optimize_slide,
    validate_config,
)


# ── Helpers ──────────────────────────────────────────────────────


def _write_minimal_presentation(tmp_path: Path) -> tuple[Path, Path, Path]:
    """Write a minimal valid presentation.yaml and metrics.json.

    Returns (config_path, metrics_path, output_dir).
    """
    config = {
        "meta": {"title": "Workflow Test", "authors": ["Agent"]},
        "theme": {
            "primary": "#1E293B",
            "accent": "#6366F1",
            "fonts": {
                "heading": "Inter",
                "subheading": "Inter",
                "body": "Inter",
            },
        },
        "slides": [
            {"layout": "title", "data": {"title": "Workflow Test Deck"}},
            {"layout": "section", "data": {"title": "Content Section"}},
            {"layout": "closing", "data": {"title": "Thank You"}},
        ],
    }
    config_path = tmp_path / "presentation.yaml"
    config_path.write_text(
        yaml.dump(config, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )
    metrics_path = tmp_path / "metrics.json"
    metrics_path.write_text(json.dumps({}), encoding="utf-8")
    output_dir = tmp_path / "slides"
    return config_path, metrics_path, output_dir


# ── Workflow documentation ────────────────────────────────────────


def test_workflow_documentation_exists():
    """MULTI_AGENT_WORKFLOW constant must document all 5 workflow roles."""
    assert isinstance(MULTI_AGENT_WORKFLOW, str)
    assert len(MULTI_AGENT_WORKFLOW) > 100

    required_roles = ["RESEARCHER", "OPTIMIZER", "BUILDER", "AUDITOR"]
    for role in required_roles:
        assert role in MULTI_AGENT_WORKFLOW, (
            f"Missing role '{role}' in MULTI_AGENT_WORKFLOW documentation"
        )


# ── Step 1: List layouts (RESEARCHER phase prep) ──────────────────


def test_workflow_step1_list_layouts():
    """Workflow step 1: list_layouts returns all available layouts."""
    layouts = list_layouts()
    assert isinstance(layouts, list)
    assert len(layouts) >= 11, f"Expected >= 11 layouts, got {len(layouts)}"
    for layout in layouts:
        assert "name" in layout
        assert "description" in layout


# ── Step 2: Get layout examples ───────────────────────────────────


def test_workflow_step2_get_examples():
    """Workflow step 2: get_layout_example works for every core layout."""
    core_layouts = [
        "title", "two-column", "three-column", "data-table", "stat-grid",
        "chart", "closing", "image", "section", "quote", "timeline",
    ]
    for name in core_layouts:
        result = get_layout_example(name)
        assert "error" not in result, f"get_layout_example({name!r}) returned error: {result}"
        assert "yaml_example" in result
        assert "name" in result


# ── Step 3: Optimize a slide ─────────────────────────────────────


def test_workflow_step3_optimize_slide():
    """Workflow step 3: optimize_slide returns slides for any valid input."""
    # Simple two-column slide — may or may not need splitting
    slide = {
        "layout": "two-column",
        "data": {
            "title": "Two Column Slide",
            "left": [
                {"type": "card", "title": "Card A", "bullets": ["Point 1", "Point 2"]},
                {"type": "card", "title": "Card B", "bullets": ["Point 3", "Point 4"]},
            ],
            "right": [
                {"type": "card", "title": "Card C", "bullets": ["Point 5", "Point 6"]},
            ],
        },
    }
    result = optimize_slide(yaml.dump(slide))
    assert "error" not in result, f"optimize_slide returned error: {result}"
    assert "slides" in result
    assert isinstance(result["slides"], list)
    assert len(result["slides"]) >= 1
    assert "count" in result
    assert "was_split" in result


# ── Step 4: Build end-to-end ─────────────────────────────────────


def test_workflow_step4_build_end_to_end(tmp_path):
    """Workflow step 4: build_presentation renders slides from config and metrics."""
    config_path, metrics_path, output_dir = _write_minimal_presentation(tmp_path)

    result = build_presentation(
        config_path=str(config_path),
        metrics_path=str(metrics_path),
        output_dir=str(output_dir),
    )

    assert "error" not in result, f"build_presentation returned error: {result}"
    assert result["slide_count"] >= 1
    assert "output_dir" in result
    assert "warnings" in result
    assert "contrast_warnings" in result


# ── Step 5: Accessibility audit ───────────────────────────────────


def test_workflow_step5_accessibility_audit(tmp_path):
    """Workflow step 5: check_accessibility_output audits built HTML slides."""
    config_path, metrics_path, output_dir = _write_minimal_presentation(tmp_path)

    # Build first so there is something to audit
    build_result = build_presentation(
        config_path=str(config_path),
        metrics_path=str(metrics_path),
        output_dir=str(output_dir),
    )
    assert "error" not in build_result, f"Build failed: {build_result}"

    result = check_accessibility_output(str(output_dir))
    assert "error" not in result, f"check_accessibility_output returned error: {result}"
    assert "pass" in result
    assert "warnings" in result
    assert "warning_count" in result
    assert isinstance(result["warnings"], list)


# ── Full sequence smoke test ──────────────────────────────────────


def test_workflow_full_sequence(tmp_path):
    """Full 5-step workflow: list -> example -> optimize -> build -> audit."""
    # Step 1: list layouts (discovery)
    layouts = list_layouts()
    assert len(layouts) >= 11

    # Step 2: get a layout example to understand data shape
    example = get_layout_example("title")
    assert "error" not in example
    assert "yaml_example" in example

    # Step 3: optimize a sample slide
    sample_slide = {
        "layout": "title",
        "data": {"title": "Full Workflow Demo"},
    }
    opt_result = optimize_slide(yaml.dump(sample_slide))
    assert "slides" in opt_result
    assert opt_result["was_split"] is False  # title slides never split

    # Step 4: build a real presentation
    config_path, metrics_path, output_dir = _write_minimal_presentation(tmp_path)
    build_result = build_presentation(
        config_path=str(config_path),
        metrics_path=str(metrics_path),
        output_dir=str(output_dir),
    )
    assert "error" not in build_result, f"Build failed in full sequence: {build_result}"
    assert build_result["slide_count"] >= 1

    # Step 5: audit accessibility of built output
    audit_result = check_accessibility_output(str(output_dir))
    assert "error" not in audit_result, f"Audit failed in full sequence: {audit_result}"
    assert "pass" in audit_result
    assert "warnings" in audit_result

    # The full chain completed without any errors
    assert True, "Full multi-agent workflow sequence completed successfully"


# ── validate_config integration ───────────────────────────────────


def test_workflow_validate_generated_config(tmp_path):
    """Workflow optional: validate_config checks the generated YAML before building."""
    config_path, _, _ = _write_minimal_presentation(tmp_path)

    result = validate_config(config_path=str(config_path))
    assert "error" not in result
    assert result["valid"] is True
    assert result["errors"] == []
