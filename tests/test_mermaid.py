"""Tests for Mermaid diagram embedding (MEDIA-03)."""
import pytest
from pf.builder import PresentationBuilder

THEME = {
    "primary": "#1C2537",
    "accent": "#C4A962",
    "fonts": {"heading": "Playfair Display", "subheading": "Montserrat", "body": "Lato"},
}


def _render(slides, primary="#1C2537"):
    b = PresentationBuilder()
    theme = {"primary": primary, "accent": "#C4A962", "fonts": THEME["fonts"]}
    b.config = {"meta": {"title": "T"}, "theme": theme, "slides": slides}
    b.metrics = {}
    features = b._scan_features(slides)
    return [b.render_slide(s, i, features=features) for i, s in enumerate(slides)]


class TestMermaidLayout:
    def test_renders_mermaid_div(self):
        htmls = _render([{"layout": "mermaid", "data": {"title": "Arch", "diagram": "graph LR; A-->B"}}])
        assert 'class="mermaid"' in htmls[0] or "class='mermaid'" in htmls[0]

    def test_diagram_text_in_output(self):
        htmls = _render([{"layout": "mermaid", "data": {"title": "Arch", "diagram": "graph LR; A-->B"}}])
        assert "graph LR" in htmls[0]

    def test_mermaid_cdn_injected(self):
        htmls = _render([{"layout": "mermaid", "data": {"title": "T", "diagram": "graph LR"}}])
        assert "mermaid" in htmls[0].lower()

    def test_no_mermaid_cdn_without_mermaid(self):
        htmls = _render([{"layout": "section", "data": {"title": "Hello"}}])
        assert "mermaid.min.js" not in htmls[0]

    def test_data_pf_ready_sentinel(self):
        htmls = _render([{"layout": "mermaid", "data": {"title": "T", "diagram": "graph LR"}}])
        assert "data-pf-ready" in htmls[0]


class TestMermaidBlock:
    def test_mermaid_block_in_two_column(self):
        slides = [{"layout": "two-column", "data": {
            "title": "T",
            "left": [{"type": "mermaid", "diagram": "sequenceDiagram; A->>B: Hi"}],
            "right": [],
        }}]
        htmls = _render(slides)
        assert "mermaid" in htmls[0]
