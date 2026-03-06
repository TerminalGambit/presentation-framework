"""Tests for code syntax highlighting (MEDIA-01)."""
import pytest
from pf.builder import PresentationBuilder, _is_light

THEME_BASE = {
    "primary": "#1C2537",
    "accent": "#C4A962",
    "fonts": {"heading": "Playfair Display", "subheading": "Montserrat", "body": "Lato"},
}


def _render(slides, primary="#1C2537"):
    """Helper: render slides and return list of HTML strings."""
    b = PresentationBuilder()
    b.config = {
        "meta": {"title": "Test"},
        "theme": {
            **THEME_BASE,
            "primary": primary,
        },
        "slides": slides,
    }
    b.metrics = {}
    features = b._scan_features(slides)
    return [b.render_slide(s, i, features=features) for i, s in enumerate(slides)]


class TestCodeLayout:
    """Full-slide code layout."""

    def test_renders_language_class(self):
        htmls = _render([{"layout": "code", "data": {"title": "T", "language": "python", "code": "x=1"}}])
        assert "language-python" in htmls[0]

    def test_renders_code_content_escaped(self):
        htmls = _render([{"layout": "code", "data": {"title": "T", "language": "html", "code": "<div>hi</div>"}}])
        assert "&lt;div&gt;" in htmls[0]

    def test_renders_caption(self):
        htmls = _render([{"layout": "code", "data": {"title": "T", "code": "x=1", "caption": "Example"}}])
        assert "Example" in htmls[0]
        assert "pf-code-caption" in htmls[0]

    def test_no_caption_when_absent(self):
        htmls = _render([{"layout": "code", "data": {"title": "T", "code": "x=1"}}])
        assert "pf-code-caption" not in htmls[0]

    def test_line_numbers_attribute(self):
        htmls = _render([{"layout": "code", "data": {"title": "T", "code": "x=1", "line_numbers": True}}])
        assert "data-line-numbers" in htmls[0]

    def test_no_line_numbers_by_default(self):
        htmls = _render([{"layout": "code", "data": {"title": "T", "code": "x=1"}}])
        assert "data-line-numbers" not in htmls[0]

    def test_fullslide_class(self):
        htmls = _render([{"layout": "code", "data": {"title": "T", "code": "x=1"}}])
        assert "pf-code-fullslide" in htmls[0]


class TestCodeCDN:
    """CDN auto-detection for Highlight.js."""

    def test_cdn_injected_for_code_layout(self):
        htmls = _render([{"layout": "code", "data": {"title": "T", "code": "x=1"}}])
        assert "highlight.js" in htmls[0] or "hljs" in htmls[0]

    def test_no_cdn_without_code(self):
        htmls = _render([{"layout": "section", "data": {"title": "Hello"}}])
        html = htmls[0]
        assert "highlight.js" not in html
        assert "hljs" not in html

    def test_cdn_for_code_block_type(self):
        slides = [{"layout": "two-column", "data": {
            "title": "T",
            "left": [{"type": "code", "code": "x=1", "language": "python"}],
            "right": []
        }}]
        htmls = _render(slides)
        assert "highlight.js" in htmls[0] or "hljs" in htmls[0]


class TestCodeThemeSelection:
    """Highlight.js theme auto-matches slide background."""

    def test_dark_background_uses_github_dark(self):
        htmls = _render(
            [{"layout": "code", "data": {"title": "T", "code": "x=1"}}],
            primary="#1C2537",  # dark
        )
        assert "github-dark" in htmls[0]

    def test_light_background_uses_github(self):
        htmls = _render(
            [{"layout": "code", "data": {"title": "T", "code": "x=1"}}],
            primary="#FFFFFF",  # light
        )
        # Should contain 'github' but not 'github-dark'
        html = htmls[0]
        assert "github.min.css" in html or ("github" in html and "github-dark" not in html)


class TestCodeBlockPartial:
    """Code as a block type in columnar layouts."""

    def test_code_block_in_two_column(self):
        slides = [{"layout": "two-column", "data": {
            "title": "T",
            "left": [{"type": "code", "language": "js", "code": "let x = 1;"}],
            "right": [],
        }}]
        htmls = _render(slides)
        assert "language-js" in htmls[0]
        assert "let x = 1;" in htmls[0] or "let x = 1" in htmls[0]

    def test_code_block_language_badge(self):
        slides = [{"layout": "two-column", "data": {
            "title": "T",
            "left": [{"type": "code", "language": "python", "code": "pass"}],
            "right": [],
        }}]
        htmls = _render(slides)
        assert "pf-code-lang-badge" in htmls[0]

    def test_auto_language_no_badge(self):
        slides = [{"layout": "two-column", "data": {
            "title": "T",
            "left": [{"type": "code", "language": "auto", "code": "pass"}],
            "right": [],
        }}]
        htmls = _render(slides)
        assert "pf-code-lang-badge" not in htmls[0]
