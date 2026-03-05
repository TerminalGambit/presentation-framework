"""Tests for inline speaker notes in present.html."""
import json
from pathlib import Path
import re

import pytest
import yaml

from pf.builder import PresentationBuilder


@pytest.fixture
def minimal_config(tmp_path):
    """Create a minimal presentation with notes on some slides."""
    config = {
        "meta": {"title": "Notes Test"},
        "theme": {"primary": "#1C2537", "accent": "#C4A962", "fonts": {"heading": "Playfair Display", "subheading": "Montserrat", "body": "Lato"}},
        "slides": [
            {
                "layout": "section",
                "data": {"title": "Slide One"},
                "notes": "These are notes for slide one.",
            },
            {
                "layout": "section",
                "data": {"title": "Slide Two"},
            },
            {
                "layout": "section",
                "data": {"title": "Slide Three"},
                "notes": 'Notes for slide three with "quotes" and <html>.',
            },
        ],
    }

    config_path = tmp_path / "presentation.yaml"
    config_path.write_text(yaml.dump(config), encoding="utf-8")
    metrics_path = tmp_path / "metrics.json"
    metrics_path.write_text("{}", encoding="utf-8")
    return tmp_path, config_path, metrics_path


def test_notes_array_embedded_in_present_html(minimal_config):
    """present.html should contain a NOTES JS array with per-slide notes."""
    tmp_path, config_path, metrics_path = minimal_config
    builder = PresentationBuilder(str(config_path), str(metrics_path))
    out = builder.build(str(tmp_path / "slides"))

    present = (out / "present.html").read_text(encoding="utf-8")

    assert "const NOTES =" in present

    match = re.search(r"const NOTES = (\[.*?\]);", present, re.DOTALL)
    assert match, "Could not find NOTES array in present.html"
    notes = json.loads(match.group(1))

    assert len(notes) == 3
    assert notes[0] == "These are notes for slide one."
    assert notes[1] == ""
    assert "quotes" in notes[2]


def test_loadnotes_uses_notes_array(minimal_config):
    """loadNotes() should read from NOTES array, not iframe contentDocument."""
    tmp_path, config_path, metrics_path = minimal_config
    builder = PresentationBuilder(str(config_path), str(metrics_path))
    out = builder.build(str(tmp_path / "slides"))

    present = (out / "present.html").read_text(encoding="utf-8")

    # The new approach should reference NOTES[current - 1]
    assert "NOTES[" in present
