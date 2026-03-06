"""Tests for per-slide custom CSS via style: key (MEDIA-06)."""
import pytest
from pf.builder import PresentationBuilder


THEME_BASE = {
    "primary": "#1C2537",
    "accent": "#C4A962",
    "fonts": {"heading": "Playfair Display", "subheading": "Montserrat", "body": "Lato"},
}


def _render(slides):
    b = PresentationBuilder()
    b.config = {
        "meta": {"title": "T"},
        "theme": THEME_BASE,
        "slides": slides,
    }
    b.metrics = {}
    features = b._scan_features(slides)
    return [b.render_slide(s, i, features=features) for i, s in enumerate(slides)]


class TestPerSlideCSS:
    """The style: key on a slide injects inline CSS into the container."""

    def test_style_injected(self):
        slides = [{"layout": "section", "data": {"title": "Styled"}, "style": "background: red;"}]
        htmls = _render(slides)
        assert "background: red;" in htmls[0]

    def test_no_style_key_no_injection(self):
        slides = [{"layout": "section", "data": {"title": "Normal"}}]
        htmls = _render(slides)
        # Should not have any orphan style injection
        assert "background: red;" not in htmls[0]

    def test_gradient_style(self):
        slides = [{"layout": "section", "data": {"title": "Grad"}, "style": "background: linear-gradient(135deg, #1C2537, #2a3a5c);"}]
        htmls = _render(slides)
        assert "linear-gradient" in htmls[0]

    def test_style_on_two_column(self):
        slides = [{"layout": "two-column", "data": {"title": "T", "left": [], "right": []}, "style": "border: 2px solid gold;"}]
        htmls = _render(slides)
        assert "border: 2px solid gold;" in htmls[0]

    def test_multiple_slides_independent_styles(self):
        slides = [
            {"layout": "section", "data": {"title": "A"}, "style": "color: red;"},
            {"layout": "section", "data": {"title": "B"}, "style": "color: blue;"},
        ]
        htmls = _render(slides)
        assert "color: red;" in htmls[0]
        assert "color: blue;" in htmls[1]
        assert "color: blue;" not in htmls[0]

    def test_style_in_slide_container_attribute(self):
        """Style should appear in the slide-container div's style attribute."""
        slides = [{"layout": "section", "data": {"title": "S"}, "style": "opacity: 0.9;"}]
        htmls = _render(slides)
        assert "opacity: 0.9;" in htmls[0]
        # Verify it's in the container div (not just anywhere in the document)
        assert 'slide-container' in htmls[0]

    def test_toc_slide_accepts_style(self):
        slides = [{"layout": "toc", "data": {"title": "TOC", "items": []}, "style": "background: #000;"}]
        htmls = _render(slides)
        assert "background: #000;" in htmls[0]
