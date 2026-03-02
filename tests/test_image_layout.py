"""Tests for image layout."""
import json
import tempfile
from pathlib import Path
import yaml
import pytest
from pf.builder import PresentationBuilder


class TestImageLayout:
    def test_render_image_full(self):
        b = PresentationBuilder()
        b.config = {
            "meta": {"title": "Test"},
            "theme": {"fonts": {"heading": "Playfair Display", "subheading": "Montserrat", "body": "Lato"}},
        }
        slide = {
            "layout": "image",
            "data": {
                "image": "assets/diagram.png",
                "position": "full",
                "title": "Architecture",
                "caption": "System overview",
            },
        }
        html = b.render_slide(slide, 0)
        assert "Architecture" in html
        assert "diagram.png" in html
        assert "System overview" in html

    def test_render_image_split(self):
        b = PresentationBuilder()
        b.config = {
            "meta": {"title": "Test"},
            "theme": {"fonts": {"heading": "Playfair Display", "subheading": "Montserrat", "body": "Lato"}},
        }
        slide = {
            "layout": "image",
            "data": {
                "image": "assets/photo.jpg",
                "position": "split",
                "side": "left",
                "title": "Our Team",
                "caption": "Founded 2024",
            },
        }
        html = b.render_slide(slide, 0)
        assert "Our Team" in html
        assert "photo.jpg" in html
