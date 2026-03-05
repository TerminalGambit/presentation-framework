"""Tests for timeline layout."""
from pf.builder import PresentationBuilder


class TestTimelineLayout:
    def test_render_timeline_slide(self):
        b = PresentationBuilder()
        b.config = {
            "meta": {"title": "Test"},
            "theme": {"fonts": {"heading": "Playfair Display", "subheading": "Montserrat", "body": "Lato"}},
        }
        slide = {
            "layout": "timeline",
            "data": {
                "title": "Our Process",
                "steps": [
                    {"icon": "search", "title": "Research", "description": "Gather requirements"},
                    {"icon": "pencil", "title": "Design", "description": "Create mockups"},
                    {"icon": "code", "title": "Build", "description": "Implement solution"},
                    {"icon": "check", "title": "Deploy", "description": "Ship to production"},
                ],
            },
        }
        html = b.render_slide(slide, 0)
        assert "Our Process" in html
        assert "Research" in html
        assert "Deploy" in html
        assert "Gather requirements" in html
