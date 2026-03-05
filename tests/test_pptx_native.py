"""Tests for pf.pptx_native editable PowerPoint export."""

import pytest
from pptx.util import Pt, Inches, Emu
from pptx.dml.color import RGBColor


class TestPptxTheme:
    def test_hex_to_rgb(self):
        from pf.pptx_native import _hex_to_rgb
        assert _hex_to_rgb("#C4A962") == RGBColor(0xC4, 0xA9, 0x62)

    def test_pptx_theme_colors(self):
        from pf.pptx_native import _pptx_theme
        theme_cfg = {"primary": "#1C2537", "accent": "#C4A962"}
        t = _pptx_theme(theme_cfg)
        assert t["primary"] == RGBColor(0x1C, 0x25, 0x37)
        assert t["accent"] == RGBColor(0xC4, 0xA9, 0x62)
        assert t["white"] == RGBColor(0xFF, 0xFF, 0xFF)
        assert t["text_muted"] == RGBColor(0xAA, 0xAA, 0xAA)

    def test_pptx_theme_fonts(self):
        from pf.pptx_native import _pptx_theme
        theme_cfg = {
            "primary": "#1C2537", "accent": "#C4A962",
            "fonts": {"heading": "Playfair Display", "subheading": "Montserrat", "body": "Lato"},
        }
        t = _pptx_theme(theme_cfg)
        assert t["font_heading"] == "Playfair Display"
        assert t["font_body"] == "Lato"

    def test_pptx_theme_defaults(self):
        from pf.pptx_native import _pptx_theme
        t = _pptx_theme({})
        assert t["primary"] == RGBColor(0x1C, 0x25, 0x37)
        assert t["font_heading"] == "Playfair Display"
