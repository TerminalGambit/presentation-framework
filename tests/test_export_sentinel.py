"""Tests for data-pf-ready sentinel in rendered HTML (EXPORT-01)."""
from pf.builder import PresentationBuilder

_BASE_THEME = {
    "primary": "#1C2537",
    "accent": "#C4A962",
    "fonts": {"heading": "Playfair Display", "subheading": "Montserrat", "body": "Lato"},
}


def _render(slides):
    b = PresentationBuilder()
    b.config = {"meta": {"title": "T"}, "theme": _BASE_THEME, "slides": slides}
    b.metrics = {}
    features = b._scan_features(slides)
    return [b.render_slide(s, i, features=features) for i, s in enumerate(slides)]


class TestSentinel:
    def test_static_slide_has_sentinel(self):
        htmls = _render([{"layout": "section", "data": {"title": "Hello"}}])
        assert "data-pf-ready" in htmls[0]

    def test_code_slide_has_sentinel(self):
        htmls = _render([{"layout": "code", "data": {"title": "T", "code": "x=1"}}])
        assert "data-pf-ready" in htmls[0]

    def test_mermaid_slide_has_sentinel(self):
        htmls = _render([{"layout": "mermaid", "data": {"title": "T", "diagram": "graph LR"}}])
        assert "data-pf-ready" in htmls[0]

    def test_map_slide_has_sentinel(self):
        htmls = _render([{"layout": "map", "data": {"title": "T", "lat": 0, "lng": 0}}])
        assert "data-pf-ready" in htmls[0]

    def test_two_column_has_sentinel(self):
        htmls = _render([{"layout": "two-column", "data": {"title": "T", "left": [], "right": []}}])
        assert "data-pf-ready" in htmls[0]
