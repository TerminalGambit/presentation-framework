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


# ── Layout renderers ─────────────────────────────────────────────

def _render_section(slide, data: dict, theme: dict):
    """Render section divider: number + title + subtitle + accent bars."""
    _add_bg(slide, theme["primary"])

    center_x = SLIDE_WIDTH // 2
    y_cursor = Inches(2.0)

    # Top accent bar
    bar_w, bar_h = Inches(1.25), Inches(0.03)
    _add_rect(slide, center_x - bar_w // 2, y_cursor, bar_w, bar_h, theme["accent"])
    y_cursor += Inches(0.5)

    # Number (optional)
    if data.get("number") is not None:
        box_w, box_h = Inches(4), Inches(0.9)
        txBox = slide.shapes.add_textbox(center_x - box_w // 2, y_cursor, box_w, box_h)
        _set_text(txBox.text_frame, f"{data['number']:02d}", theme["font_heading"], 60, theme["accent"], bold=True)
        y_cursor += Inches(0.9)

    # Title
    box_w, box_h = Inches(10), Inches(1.2)
    txBox = slide.shapes.add_textbox(center_x - box_w // 2, y_cursor, box_w, box_h)
    _set_text(txBox.text_frame, data["title"], theme["font_heading"], 48, theme["white"], bold=True)
    y_cursor += Inches(1.2)

    # Subtitle (optional)
    if data.get("subtitle"):
        box_w, box_h = Inches(10), Inches(0.6)
        txBox = slide.shapes.add_textbox(center_x - box_w // 2, y_cursor, box_w, box_h)
        _set_text(txBox.text_frame, data["subtitle"].upper(), theme["font_subheading"], 18, theme["text_muted"])
        y_cursor += Inches(0.7)

    # Bottom accent bar
    _add_rect(slide, center_x - bar_w // 2, y_cursor, bar_w, bar_h, theme["accent"])


def _render_quote(slide, data: dict, theme: dict):
    """Render quote: quotation mark + text + divider + attribution."""
    _add_bg(slide, theme["primary"])
    center_x = SLIDE_WIDTH // 2
    y_cursor = Inches(1.5)

    # Quotation mark
    box_w, box_h = Inches(2), Inches(1.2)
    txBox = slide.shapes.add_textbox(center_x - box_w // 2, y_cursor, box_w, box_h)
    _set_text(txBox.text_frame, "\u201C", theme["font_heading"], 96, theme["accent"])
    y_cursor += Inches(1.0)

    # Quote text
    box_w, box_h = Inches(9), Inches(2.0)
    txBox = slide.shapes.add_textbox(center_x - box_w // 2, y_cursor, box_w, box_h)
    _set_text(txBox.text_frame, data["text"], theme["font_heading"], 28, theme["white"])
    txBox.text_frame.word_wrap = True
    y_cursor += Inches(1.8)

    # Divider
    bar_w, bar_h = Inches(0.8), Inches(0.03)
    _add_rect(slide, center_x - bar_w // 2, y_cursor, bar_w, bar_h, theme["accent"])
    y_cursor += Inches(0.4)

    # Attribution
    parts = []
    if data.get("author"):
        parts.append(data["author"])
    if data.get("role"):
        parts.append(data["role"])
    if parts:
        box_w, box_h = Inches(8), Inches(0.8)
        txBox = slide.shapes.add_textbox(center_x - box_w // 2, y_cursor, box_w, box_h)
        _set_text(txBox.text_frame, " — ".join(parts), theme["font_subheading"], 16, theme["text_muted"])


def _render_closing(slide, data: dict, theme: dict):
    """Render closing: title + subtitle + divider."""
    _add_bg(slide, theme["primary"])
    center_x = SLIDE_WIDTH // 2
    y_cursor = Inches(2.2)

    # Title
    box_w, box_h = Inches(10), Inches(1.5)
    txBox = slide.shapes.add_textbox(center_x - box_w // 2, y_cursor, box_w, box_h)
    _set_text(txBox.text_frame, data["title"], theme["font_heading"], 60, theme["accent"], bold=True)
    y_cursor += Inches(1.5)

    # Divider
    bar_w, bar_h = Inches(1.5), Inches(0.03)
    _add_rect(slide, center_x - bar_w // 2, y_cursor, bar_w, bar_h, theme["accent"])
    y_cursor += Inches(0.5)

    # Subtitle
    if data.get("subtitle"):
        box_w, box_h = Inches(10), Inches(0.8)
        txBox = slide.shapes.add_textbox(center_x - box_w // 2, y_cursor, box_w, box_h)
        _set_text(txBox.text_frame, data["subtitle"], theme["font_subheading"], 20, theme["text_muted"])


def _render_title(slide, data: dict, theme: dict):
    """Render title slide: hero title + subtitle + optional feature labels."""
    _add_bg(slide, theme["primary"])
    center_x = SLIDE_WIDTH // 2

    # Hero title
    box_w, box_h = Inches(10), Inches(2)
    txBox = slide.shapes.add_textbox(center_x - box_w // 2, Inches(1.8), box_w, box_h)
    _set_text(txBox.text_frame, data.get("title", ""), theme["font_heading"], 60, theme["accent"], bold=True)
    txBox.text_frame.word_wrap = True

    # Subtitle
    if data.get("subtitle"):
        box_w, box_h = Inches(10), Inches(0.8)
        txBox = slide.shapes.add_textbox(center_x - box_w // 2, Inches(3.9), box_w, box_h)
        _set_text(txBox.text_frame, data["subtitle"], theme["font_subheading"], 20, theme["text_muted"])
        txBox.text_frame.word_wrap = True

    # Features (icon labels across bottom)
    features = data.get("features", [])
    if features:
        total_w = len(features) * Inches(2.5)
        x_start = center_x - total_w // 2
        for i, feat in enumerate(features):
            box_x = x_start + i * Inches(2.5)
            txBox = slide.shapes.add_textbox(box_x, Inches(5.2), Inches(2.2), Inches(0.6))
            label = feat.get("label", feat) if isinstance(feat, dict) else str(feat)
            _set_text(txBox.text_frame, label, theme["font_body"], 12, theme["text_muted"])


def _render_stat_grid(slide, data: dict, theme: dict):
    """Render stat-grid: title + grid of stat boxes with values and labels."""
    import math
    _add_bg(slide, theme["primary"])
    center_x = SLIDE_WIDTH // 2

    # Title
    if data.get("title"):
        box_w = Inches(10)
        txBox = slide.shapes.add_textbox(center_x - box_w // 2, Inches(0.5), box_w, Inches(0.8))
        _set_text(txBox.text_frame, data["title"], theme["font_heading"], 36, theme["accent"], bold=True)

    stats = data.get("stats", [])
    cols = data.get("cols", min(len(stats), 4))
    if not stats or cols == 0:
        return

    rows = math.ceil(len(stats) / cols)
    card_w = Inches(2.8)
    card_h = Inches(1.8)
    gap = Inches(0.3)
    total_w = cols * card_w + (cols - 1) * gap
    x_start = center_x - total_w // 2
    y_start = Inches(1.8)

    for idx, stat in enumerate(stats):
        row = idx // cols
        col = idx % cols
        x = x_start + col * (card_w + gap)
        y = y_start + row * (card_h + gap)

        # Stat card background
        _add_rect(slide, x, y, card_w, card_h, _hex_to_rgb("#1a2236"))

        # Value
        txBox = slide.shapes.add_textbox(x + Inches(0.2), y + Inches(0.3), card_w - Inches(0.4), Inches(0.8))
        value = str(stat.get("value", ""))
        _set_text(txBox.text_frame, value, theme["font_heading"], 36, theme["accent"], bold=True)

        # Label
        txBox = slide.shapes.add_textbox(x + Inches(0.2), y + Inches(1.1), card_w - Inches(0.4), Inches(0.5))
        label = stat.get("label", "")
        _set_text(txBox.text_frame, label, theme["font_body"], 12, theme["text_muted"])


def _render_two_column(slide, data: dict, theme: dict):
    """Render two-column: title + left/right columns with card/insight blocks."""
    _add_bg(slide, theme["primary"])
    center_x = SLIDE_WIDTH // 2

    # Title
    if data.get("title"):
        box_w = Inches(12)
        txBox = slide.shapes.add_textbox(center_x - box_w // 2, Inches(0.3), box_w, Inches(0.8))
        _set_text(txBox.text_frame, data["title"], theme["font_heading"], 36, theme["accent"], bold=True,
                  alignment=PP_ALIGN.LEFT)

    col_w = Inches(5.8)
    left_x = Inches(0.5)
    right_x = Inches(7.0)
    y_start = Inches(1.4)

    def render_column(blocks, x_start):
        y = y_start
        for block in blocks:
            btype = block.get("type", "card")
            if btype == "card":
                card_h = Inches(0.8) + Inches(0.25) * len(block.get("bullets", []))
                # Card background
                _add_rect(slide, x_start, y, col_w, card_h, _hex_to_rgb("#1a2236"))
                # Card title
                if block.get("title"):
                    txBox = slide.shapes.add_textbox(
                        x_start + Inches(0.2), y + Inches(0.1), col_w - Inches(0.4), Inches(0.4))
                    _set_text(txBox.text_frame, block["title"], theme["font_subheading"], 14, theme["accent"],
                              bold=True, alignment=PP_ALIGN.LEFT)
                # Card text
                if block.get("text"):
                    txBox = slide.shapes.add_textbox(
                        x_start + Inches(0.2), y + Inches(0.45), col_w - Inches(0.4), Inches(0.35))
                    _set_text(txBox.text_frame, block["text"], theme["font_body"], 11, theme["white"],
                              alignment=PP_ALIGN.LEFT)
                    txBox.text_frame.word_wrap = True
                y += card_h + Inches(0.15)
            elif btype == "insight":
                txBox = slide.shapes.add_textbox(x_start, y, col_w, Inches(0.5))
                _set_text(txBox.text_frame, block.get("text", ""), theme["font_body"], 11, theme["text_muted"],
                          alignment=PP_ALIGN.LEFT)
                txBox.text_frame.word_wrap = True
                y += Inches(0.55)
            else:
                # Unsupported block type in native — skip with spacing
                y += Inches(0.5)

    render_column(data.get("left", []), left_x)
    render_column(data.get("right", []), right_x)


def _render_three_column(slide, data: dict, theme: dict):
    """Render three-column: title + 3 columns with card blocks."""
    _add_bg(slide, theme["primary"])
    center_x = SLIDE_WIDTH // 2

    # Title
    if data.get("title"):
        box_w = Inches(12)
        txBox = slide.shapes.add_textbox(center_x - box_w // 2, Inches(0.3), box_w, Inches(0.8))
        _set_text(txBox.text_frame, data["title"], theme["font_heading"], 36, theme["accent"], bold=True,
                  alignment=PP_ALIGN.LEFT)

    columns = data.get("columns", [[], [], []])
    num_cols = len(columns)
    if num_cols == 0:
        return

    col_w = Inches(3.6)
    gap = Inches(0.3)
    total_w = num_cols * col_w + (num_cols - 1) * gap
    x_start = center_x - total_w // 2
    y_start = Inches(1.4)

    for col_idx, col_blocks in enumerate(columns):
        x = x_start + col_idx * (col_w + gap)
        y = y_start
        if not isinstance(col_blocks, list):
            continue
        for block in col_blocks:
            btype = block.get("type", "card")
            if btype == "card":
                card_h = Inches(0.8) + Inches(0.25) * len(block.get("bullets", []))
                _add_rect(slide, x, y, col_w, card_h, _hex_to_rgb("#1a2236"))
                if block.get("title"):
                    txBox = slide.shapes.add_textbox(
                        x + Inches(0.15), y + Inches(0.1), col_w - Inches(0.3), Inches(0.4))
                    _set_text(txBox.text_frame, block["title"], theme["font_subheading"], 13, theme["accent"],
                              bold=True, alignment=PP_ALIGN.LEFT)
                if block.get("text"):
                    txBox = slide.shapes.add_textbox(
                        x + Inches(0.15), y + Inches(0.45), col_w - Inches(0.3), Inches(0.3))
                    _set_text(txBox.text_frame, block["text"], theme["font_body"], 10, theme["white"],
                              alignment=PP_ALIGN.LEFT)
                    txBox.text_frame.word_wrap = True
                y += card_h + Inches(0.15)
            else:
                y += Inches(0.5)


# ── Layout dispatch ──────────────────────────────────────────────

NATIVE_RENDERERS = {
    "section": _render_section,
    "quote": _render_quote,
    "closing": _render_closing,
    "title": _render_title,
    "stat-grid": _render_stat_grid,
    "two-column": _render_two_column,
    "three-column": _render_three_column,
}


def _render_image_fallback(slide, slide_file: Path, context=None):
    """Fall back to screenshot for complex layouts (requires Playwright).

    Args:
        slide: python-pptx slide object to add the screenshot to.
        slide_file: Path to the slide HTML file.
        context: Optional shared Playwright browser context. If provided,
            reuses it instead of spawning a new browser per slide.
    """
    if context:
        page = context.new_page()
        page.goto(f"file://{slide_file.resolve()}")
        page.wait_for_load_state("networkidle")
        try:
            page.wait_for_selector("[data-pf-ready]", timeout=10000)
        except Exception:
            pass  # Graceful fallback if sentinel missing
        png_bytes = page.screenshot(full_page=False)
        page.close()
    else:
        # Legacy path — spawns own browser (no shared context available)
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            return  # Skip if Playwright unavailable

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 720})
            page.goto(f"file://{slide_file.resolve()}")
            page.wait_for_load_state("networkidle")
            try:
                page.wait_for_selector("[data-pf-ready]", timeout=10000)
            except Exception:
                pass  # Graceful fallback if sentinel missing
            png_bytes = page.screenshot(full_page=False)
            page.close()
            browser.close()

    slide.shapes.add_picture(
        io.BytesIO(png_bytes),
        left=Emu(0), top=Emu(0),
        width=SLIDE_WIDTH, height=SLIDE_HEIGHT,
    )


def export_pptx_editable(
    config: dict,
    slides_dir: str,
    output_path: str,
):
    """Export slides to an editable .pptx file.

    Native text/shapes for supported layouts (section, quote, closing,
    title, stat-grid, two-column, three-column). Image fallback via
    Playwright for complex layouts. Uses a single shared browser context
    across all image fallbacks to avoid spawning a browser per slide.
    """
    prs = Presentation()
    prs.slide_width = SLIDE_WIDTH
    prs.slide_height = SLIDE_HEIGHT
    blank_layout = prs.slide_layouts[6]

    theme = _pptx_theme(config.get("theme", {}))
    slides_path = Path(slides_dir)
    slides_cfg = config.get("slides", [])

    # Create shared browser context for image fallbacks (EXPORT-04)
    pw_manager = None
    pw_browser = None
    pw_context = None
    try:
        from playwright.sync_api import sync_playwright
        pw_manager = sync_playwright().start()
        pw_browser = pw_manager.chromium.launch()
        pw_context = pw_browser.new_context(viewport={"width": 1280, "height": 720})
    except (ImportError, Exception):
        pass  # Playwright unavailable — image fallback will skip gracefully

    try:
        for i, slide_cfg in enumerate(slides_cfg):
            layout = slide_cfg.get("layout", "two-column")
            data = slide_cfg.get("data", {})
            slide = prs.slides.add_slide(blank_layout)

            renderer = NATIVE_RENDERERS.get(layout)
            if renderer:
                renderer(slide, data, theme)
            else:
                slide_file = slides_path / f"slide_{i + 1:02d}.html"
                if slide_file.exists():
                    _render_image_fallback(slide, slide_file, context=pw_context)

            # Speaker notes
            if slide_cfg.get("notes"):
                slide.notes_slide.notes_text_frame.text = slide_cfg["notes"]
    finally:
        # Always clean up shared browser context
        if pw_context:
            pw_context.close()
        if pw_browser:
            pw_browser.close()
        if pw_manager:
            pw_manager.stop()

    prs.save(output_path)
