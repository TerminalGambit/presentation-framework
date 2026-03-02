"""Tests for quote layout."""
from pf.builder import PresentationBuilder


class TestQuoteLayout:
    def test_render_quote_slide(self):
        b = PresentationBuilder()
        b.config = {
            "meta": {"title": "Test"},
            "theme": {"fonts": {"heading": "Playfair Display", "subheading": "Montserrat", "body": "Lato"}},
        }
        slide = {
            "layout": "quote",
            "data": {
                "text": "The best way to predict the future is to invent it.",
                "author": "Alan Kay",
                "role": "Computer Scientist",
            },
        }
        html = b.render_slide(slide, 0)
        assert "The best way to predict the future" in html
        assert "Alan Kay" in html
        assert "Computer Scientist" in html
