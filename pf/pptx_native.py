"""
Editable PowerPoint export for Presentation Framework.
Requires: pip install presentation-framework[pptx]

Converts simple layouts (section, quote, closing) to native
python-pptx text boxes and shapes. Complex layouts fall back to
image-based rendering via Playwright.
"""

import io
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN


# ── Slide dimensions (16:9 at 96 DPI) ────────────────────────────
SLIDE_WIDTH = Inches(13.333)
SLIDE_HEIGHT = Inches(7.5)


# ── Theme conversion ─────────────────────────────────────────────

def _hex_to_rgb(hex_color: str) -> RGBColor:
    """Convert '#RRGGBB' to python-pptx RGBColor."""
    h = hex_color.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _pptx_theme(theme_cfg: dict) -> dict:
    """Convert presentation.yaml theme to python-pptx primitives."""
    fonts = theme_cfg.get("fonts", {})
    return {
        "primary": _hex_to_rgb(theme_cfg.get("primary", "#1C2537")),
        "accent": _hex_to_rgb(theme_cfg.get("accent", "#C4A962")),
        "white": RGBColor(0xFF, 0xFF, 0xFF),
        "text_muted": RGBColor(0xAA, 0xAA, 0xAA),
        "font_heading": fonts.get("heading", "Playfair Display"),
        "font_subheading": fonts.get("subheading", "Montserrat"),
        "font_body": fonts.get("body", "Lato"),
    }


def _set_text(text_frame, text, font_name, font_size_pt, color, bold=False, alignment=PP_ALIGN.CENTER):
    """Set text on a shape's text_frame with styling."""
    text_frame.clear()
    p = text_frame.paragraphs[0]
    p.alignment = alignment
    run = p.add_run()
    run.text = text
    run.font.name = font_name
    run.font.size = Pt(font_size_pt)
    run.font.color.rgb = color
    run.font.bold = bold


def _add_bg(slide, color):
    """Set solid background color on a slide."""
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def _add_rect(slide, left, top, width, height, color):
    """Add a colored rectangle shape."""
    from pptx.enum.shapes import MSO_SHAPE
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()  # No border
    return shape
