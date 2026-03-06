"""Tests for Phase 1 foundation infrastructure."""
import json
import pytest
from pathlib import Path
from pf.builder import PresentationBuilder, _is_light

# --- Schema tests ---

def test_schema_includes_new_layouts():
    schema = json.load(open(Path(__file__).parent.parent / "pf" / "schema.json"))
    layouts = schema["properties"]["slides"]["items"]["properties"]["layout"]["enum"]
    for name in ("code", "mermaid", "video", "map", "toc"):
        assert name in layouts, f"{name} missing from schema layout enum"

def test_schema_allows_style_key():
    schema = json.load(open(Path(__file__).parent.parent / "pf" / "schema.json"))
    props = schema["properties"]["slides"]["items"]["properties"]
    assert "style" in props

# --- Auto-detect tests ---

def test_scan_features_detects_code_layout():
    b = PresentationBuilder()
    features = b._scan_features([{"layout": "code", "data": {}}])
    assert features["code"] is True
    assert features["mermaid"] is False

def test_scan_features_detects_block_types_in_left_right():
    b = PresentationBuilder()
    slides = [{"layout": "two-column", "data": {
        "left": [{"type": "mermaid", "diagram": "graph LR"}],
        "right": [{"type": "map", "lat": 0, "lng": 0}],
    }}]
    features = b._scan_features(slides)
    assert features["mermaid"] is True
    assert features["map"] is True

def test_scan_features_detects_block_types_in_columns():
    b = PresentationBuilder()
    slides = [{"layout": "three-column", "data": {
        "columns": [[{"type": "code", "code": "x=1"}], [], [{"type": "video", "url": "https://youtube.com/watch?v=abc"}]]
    }}]
    features = b._scan_features(slides)
    assert features["code"] is True
    assert features["video"] is True

def test_scan_features_empty_slides():
    b = PresentationBuilder()
    features = b._scan_features([])
    assert all(v is False for v in features.values())

THEME_BASE = {
    "primary": "#1C2537",
    "accent": "#C4A962",
    "fonts": {"heading": "Playfair Display", "subheading": "Montserrat", "body": "Lato"},
}

# --- Sentinel tests ---

def test_sentinel_in_rendered_html(tmp_path):
    """Static slides should include data-pf-ready in their HTML."""
    config = {
        "meta": {"title": "Test"},
        "theme": THEME_BASE,
        "slides": [{"layout": "section", "data": {"title": "Hello"}}],
    }
    b = PresentationBuilder()
    b.config = config
    b.metrics = {}
    features = b._scan_features(config["slides"])
    html = b.render_slide(config["slides"][0], 0, features=features)
    assert "data-pf-ready" in html

# --- Per-slide CSS tests ---

def test_style_key_injected_in_html(tmp_path):
    """slide.style value should appear in the slide-container div."""
    config = {
        "meta": {"title": "Test"},
        "theme": THEME_BASE,
        "slides": [{"layout": "section", "data": {"title": "Styled"}, "style": "background: red;"}],
    }
    b = PresentationBuilder()
    b.config = config
    b.metrics = {}
    features = b._scan_features(config["slides"])
    html = b.render_slide(config["slides"][0], 0, features=features)
    assert "background: red;" in html

# --- is_light tests ---

def test_is_light_dark_color():
    assert _is_light("#1C2537") is False

def test_is_light_light_color():
    assert _is_light("#FFFFFF") is True

# --- CDN injection tests ---

def test_code_cdn_injected_when_code_feature(tmp_path):
    config = {
        "meta": {"title": "Test"},
        "theme": THEME_BASE,
        "slides": [{"layout": "code", "data": {"title": "Code", "code": "x=1", "language": "python"}}],
    }
    b = PresentationBuilder()
    b.config = config
    b.metrics = {}
    features = b._scan_features(config["slides"])
    html = b.render_slide(config["slides"][0], 0, features=features)
    assert "highlight.js" in html or "hljs" in html

def test_no_code_cdn_without_code_feature(tmp_path):
    config = {
        "meta": {"title": "Test"},
        "theme": THEME_BASE,
        "slides": [{"layout": "section", "data": {"title": "No Code"}}],
    }
    b = PresentationBuilder()
    b.config = config
    b.metrics = {}
    features = b._scan_features(config["slides"])
    html = b.render_slide(config["slides"][0], 0, features=features)
    assert "highlight.js" not in html
    assert "hljs" not in html

# --- Analyzer tests ---

def test_analyzer_code_block_height():
    from pf.analyzer import LayoutAnalyzer
    block = {"type": "code", "code": "x = 1"}
    height = LayoutAnalyzer.estimate_block_height(block)
    assert height > 0

def test_analyzer_mermaid_block_height():
    from pf.analyzer import LayoutAnalyzer
    block = {"type": "mermaid", "diagram": "graph LR"}
    height = LayoutAnalyzer.estimate_block_height(block)
    assert height > 0
