"""Tests for auto-generated Table of Contents (MEDIA-07)."""
import pytest
from pf.builder import PresentationBuilder


THEME_BASE = {
    "primary": "#1C2537",
    "accent": "#C4A962",
    "fonts": {"heading": "Playfair Display", "subheading": "Montserrat", "body": "Lato"},
}


class TestTOCGeneration:
    """Builder scans section slides and generates TOC entries."""

    def test_collects_sections(self):
        b = PresentationBuilder()
        slides = [
            {"layout": "title", "data": {"title": "Welcome"}},
            {"layout": "section", "data": {"number": 1, "title": "Introduction"}},
            {"layout": "two-column", "data": {"title": "Data", "left": [], "right": []}},
            {"layout": "section", "data": {"number": 2, "title": "Methods", "subtitle": "Approach"}},
            {"layout": "section", "data": {"number": 3, "title": "Results"}},
        ]
        items = b._generate_toc(slides)
        assert len(items) == 3
        assert items[0]["title"] == "Introduction"
        assert items[1]["subtitle"] == "Approach"
        assert items[2]["number"] == 3

    def test_empty_presentation(self):
        b = PresentationBuilder()
        items = b._generate_toc([])
        assert items == []

    def test_no_sections(self):
        b = PresentationBuilder()
        slides = [{"layout": "title", "data": {"title": "Hello"}}]
        items = b._generate_toc(slides)
        assert items == []

    def test_section_without_number(self):
        b = PresentationBuilder()
        slides = [{"layout": "section", "data": {"title": "Appendix"}}]
        items = b._generate_toc(slides)
        assert len(items) == 1
        assert items[0]["number"] == ""
        assert items[0]["title"] == "Appendix"

    def test_section_without_subtitle(self):
        b = PresentationBuilder()
        slides = [{"layout": "section", "data": {"number": 1, "title": "Intro"}}]
        items = b._generate_toc(slides)
        assert items[0]["subtitle"] == ""

    def test_non_section_slides_excluded(self):
        b = PresentationBuilder()
        slides = [
            {"layout": "toc", "data": {"title": "Contents"}},
            {"layout": "two-column", "data": {"title": "T", "left": [], "right": []}},
            {"layout": "section", "data": {"number": 1, "title": "Actual Section"}},
        ]
        items = b._generate_toc(slides)
        assert len(items) == 1
        assert items[0]["title"] == "Actual Section"


class TestTOCLayout:
    """TOC layout renders section entries."""

    def _render_toc(self, items, title="Contents"):
        b = PresentationBuilder()
        b.config = {
            "meta": {"title": "T"},
            "theme": THEME_BASE,
            "slides": [{"layout": "toc", "data": {"title": title, "items": items}}],
        }
        b.metrics = {}
        features = b._scan_features(b.config["slides"])
        return b.render_slide(b.config["slides"][0], 0, features=features)

    def test_renders_toc_entries(self):
        items = [{"number": 1, "title": "Intro"}, {"number": 2, "title": "Methods"}]
        html = self._render_toc(items)
        assert "Intro" in html
        assert "Methods" in html
        assert "pf-toc" in html

    def test_renders_numbers(self):
        items = [{"number": 1, "title": "Intro"}]
        html = self._render_toc(items)
        assert "01" in html or "1" in html

    def test_renders_subtitle(self):
        items = [{"number": 1, "title": "Intro", "subtitle": "Background"}]
        html = self._render_toc(items)
        assert "Background" in html

    def test_empty_items(self):
        html = self._render_toc([])
        assert "pf-toc" in html  # Container still renders

    def test_title_in_header(self):
        html = self._render_toc([{"number": 1, "title": "A"}], title="Agenda")
        assert "Agenda" in html

    def test_no_subtitle_when_absent(self):
        items = [{"number": 1, "title": "Intro"}]
        html = self._render_toc(items)
        assert "pf-toc-subtitle" not in html

    def test_subtitle_rendered_when_present(self):
        items = [{"number": 2, "title": "Methods", "subtitle": "How we did it"}]
        html = self._render_toc(items)
        assert "pf-toc-subtitle" in html
        assert "How we did it" in html
