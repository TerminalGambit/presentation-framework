"""Tests for section divider layout."""
from pf.builder import PresentationBuilder


class TestSectionLayout:
    def test_render_section_slide(self):
        b = PresentationBuilder()
        b.config = {
            "meta": {"title": "Test"},
            "theme": {"fonts": {"heading": "Playfair Display", "subheading": "Montserrat", "body": "Lato"}},
        }
        slide = {
            "layout": "section",
            "data": {
                "title": "Research Findings",
                "subtitle": "What we discovered",
                "number": 2,
            },
        }
        html = b.render_slide(slide, 0)
        assert "Research Findings" in html
        assert "What we discovered" in html
        assert "02" in html or "2" in html
