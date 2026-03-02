"""Tests for speaker notes."""
import tempfile
from pathlib import Path
import yaml
from pf.builder import PresentationBuilder


class TestSpeakerNotes:
    def test_notes_rendered_as_aside(self):
        b = PresentationBuilder()
        b.config = {
            "meta": {"title": "Test"},
            "theme": {"fonts": {"heading": "Playfair Display", "subheading": "Montserrat", "body": "Lato"}},
        }
        slide = {
            "layout": "title",
            "notes": "Remember to mention the timeline",
            "data": {"title": "Hello"},
        }
        html = b.render_slide(slide, 0)
        assert '<aside class="notes">' in html
        assert "Remember to mention the timeline" in html

    def test_no_notes_no_aside(self):
        b = PresentationBuilder()
        b.config = {
            "meta": {"title": "Test"},
            "theme": {"fonts": {"heading": "Playfair Display", "subheading": "Montserrat", "body": "Lato"}},
        }
        slide = {
            "layout": "title",
            "data": {"title": "Hello"},
        }
        html = b.render_slide(slide, 0)
        assert '<aside class="notes">' not in html
