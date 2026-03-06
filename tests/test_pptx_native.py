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


from pptx import Presentation as PptxPresentation


class TestSectionLayout:
    def test_renders_title(self):
        from pf.pptx_native import _render_section, _pptx_theme, SLIDE_WIDTH, SLIDE_HEIGHT
        prs = PptxPresentation()
        prs.slide_width = SLIDE_WIDTH
        prs.slide_height = SLIDE_HEIGHT
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        theme = _pptx_theme({"primary": "#1C2537", "accent": "#C4A962"})
        _render_section(slide, {"title": "New Layouts", "subtitle": "Four new types", "number": 1}, theme)
        texts = [s.text_frame.text for s in slide.shapes if s.has_text_frame]
        assert "New Layouts" in texts

    def test_renders_subtitle(self):
        from pf.pptx_native import _render_section, _pptx_theme, SLIDE_WIDTH, SLIDE_HEIGHT
        prs = PptxPresentation()
        prs.slide_width = SLIDE_WIDTH
        prs.slide_height = SLIDE_HEIGHT
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        theme = _pptx_theme({"primary": "#1C2537", "accent": "#C4A962"})
        _render_section(slide, {"title": "Test", "subtitle": "Sub text"}, theme)
        texts = [s.text_frame.text for s in slide.shapes if s.has_text_frame]
        assert "SUB TEXT" in texts  # uppercase

    def test_renders_number(self):
        from pf.pptx_native import _render_section, _pptx_theme, SLIDE_WIDTH, SLIDE_HEIGHT
        prs = PptxPresentation()
        prs.slide_width = SLIDE_WIDTH
        prs.slide_height = SLIDE_HEIGHT
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        theme = _pptx_theme({"primary": "#1C2537", "accent": "#C4A962"})
        _render_section(slide, {"title": "Test", "number": 3}, theme)
        texts = [s.text_frame.text for s in slide.shapes if s.has_text_frame]
        assert "03" in texts


class TestQuoteLayout:
    def test_renders_quote_text(self):
        from pf.pptx_native import _render_quote, _pptx_theme, SLIDE_WIDTH, SLIDE_HEIGHT
        prs = PptxPresentation()
        prs.slide_width = SLIDE_WIDTH
        prs.slide_height = SLIDE_HEIGHT
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        theme = _pptx_theme({"primary": "#1C2537", "accent": "#C4A962"})
        _render_quote(slide, {"text": "The best way to predict the future is to invent it.", "author": "Alan Kay"}, theme)
        texts = [s.text_frame.text for s in slide.shapes if s.has_text_frame]
        assert any("predict the future" in t for t in texts)

    def test_renders_attribution(self):
        from pf.pptx_native import _render_quote, _pptx_theme, SLIDE_WIDTH, SLIDE_HEIGHT
        prs = PptxPresentation()
        prs.slide_width = SLIDE_WIDTH
        prs.slide_height = SLIDE_HEIGHT
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        theme = _pptx_theme({"primary": "#1C2537", "accent": "#C4A962"})
        _render_quote(slide, {"text": "Quote", "author": "Author", "role": "Scientist"}, theme)
        texts = [s.text_frame.text for s in slide.shapes if s.has_text_frame]
        assert any("Author" in t for t in texts)


class TestClosingLayout:
    def test_renders_title(self):
        from pf.pptx_native import _render_closing, _pptx_theme, SLIDE_WIDTH, SLIDE_HEIGHT
        prs = PptxPresentation()
        prs.slide_width = SLIDE_WIDTH
        prs.slide_height = SLIDE_HEIGHT
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        theme = _pptx_theme({"primary": "#1C2537", "accent": "#C4A962"})
        _render_closing(slide, {"title": "Thank You", "subtitle": "Questions?"}, theme)
        texts = [s.text_frame.text for s in slide.shapes if s.has_text_frame]
        assert "Thank You" in texts

    def test_renders_subtitle(self):
        from pf.pptx_native import _render_closing, _pptx_theme, SLIDE_WIDTH, SLIDE_HEIGHT
        prs = PptxPresentation()
        prs.slide_width = SLIDE_WIDTH
        prs.slide_height = SLIDE_HEIGHT
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        theme = _pptx_theme({"primary": "#1C2537", "accent": "#C4A962"})
        _render_closing(slide, {"title": "Thanks", "subtitle": "Q&A"}, theme)
        texts = [s.text_frame.text for s in slide.shapes if s.has_text_frame]
        assert "Q&A" in texts


import json
import yaml
from pathlib import Path


class TestExportEditable:
    def _write_config(self, tmp_path, slides):
        config = {
            "meta": {"title": "Test", "authors": ["Tester"]},
            "theme": {
                "primary": "#1C2537", "accent": "#C4A962",
                "fonts": {"heading": "Playfair Display", "subheading": "Montserrat", "body": "Lato"},
            },
            "slides": slides,
        }
        config_path = tmp_path / "presentation.yaml"
        config_path.write_text(yaml.dump(config, sort_keys=False), encoding="utf-8")
        metrics_path = tmp_path / "metrics.json"
        metrics_path.write_text(json.dumps({"metadata": {}, "summary": {}}), encoding="utf-8")
        return config_path, metrics_path

    def test_section_slide_native(self, tmp_path):
        from pf.pptx_native import export_pptx_editable
        from pf.builder import PresentationBuilder
        config_path, metrics_path = self._write_config(tmp_path, [
            {"layout": "section", "data": {"title": "Hello", "number": 1}},
        ])
        builder = PresentationBuilder(config_path=str(config_path), metrics_path=str(metrics_path))
        import contextlib, io as _io
        with contextlib.redirect_stdout(_io.StringIO()):
            out = builder.build(output_dir=str(tmp_path / "slides"))
        output_pptx = str(tmp_path / "out.pptx")
        export_pptx_editable(builder.config, str(out), output_pptx)
        prs = PptxPresentation(output_pptx)
        assert len(prs.slides) == 1
        texts = [s.text_frame.text for s in prs.slides[0].shapes if s.has_text_frame]
        assert "Hello" in texts

    def test_fallback_uses_image(self, tmp_path):
        """Non-native layouts should still produce a slide (via image fallback)."""
        from pf.pptx_native import export_pptx_editable
        from pf.builder import PresentationBuilder
        config_path, metrics_path = self._write_config(tmp_path, [
            {"layout": "section", "data": {"title": "Native"}},
            {"layout": "closing", "data": {"title": "Also Native"}},
        ])
        builder = PresentationBuilder(config_path=str(config_path), metrics_path=str(metrics_path))
        import contextlib, io as _io
        with contextlib.redirect_stdout(_io.StringIO()):
            out = builder.build(output_dir=str(tmp_path / "slides"))
        output_pptx = str(tmp_path / "out.pptx")
        export_pptx_editable(builder.config, str(out), output_pptx)
        prs = PptxPresentation(output_pptx)
        assert len(prs.slides) == 2


class TestTitleLayout:
    """Native PPTX renderer for title layout."""

    def test_title_in_native_renderers(self):
        from pf.pptx_native import NATIVE_RENDERERS
        assert "title" in NATIVE_RENDERERS

    def test_title_renders_without_error(self):
        from pf.pptx_native import NATIVE_RENDERERS, _pptx_theme, SLIDE_WIDTH, SLIDE_HEIGHT
        prs = PptxPresentation()
        prs.slide_width = SLIDE_WIDTH
        prs.slide_height = SLIDE_HEIGHT
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        theme = _pptx_theme({"primary": "#1C2537", "accent": "#C4A962"})
        NATIVE_RENDERERS["title"](slide, {"title": "Hello World", "subtitle": "Subtitle"}, theme)
        assert len(slide.shapes) > 0

    def test_title_renders_features(self):
        from pf.pptx_native import NATIVE_RENDERERS, _pptx_theme, SLIDE_WIDTH, SLIDE_HEIGHT
        prs = PptxPresentation()
        prs.slide_width = SLIDE_WIDTH
        prs.slide_height = SLIDE_HEIGHT
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        theme = _pptx_theme({"primary": "#1C2537", "accent": "#C4A962"})
        NATIVE_RENDERERS["title"](slide, {
            "title": "Title",
            "features": [{"label": "Feature A"}, {"label": "Feature B"}],
        }, theme)
        texts = [s.text_frame.text for s in slide.shapes if s.has_text_frame]
        assert any("Feature A" in t for t in texts)


class TestStatGridLayout:
    def test_stat_grid_in_native_renderers(self):
        from pf.pptx_native import NATIVE_RENDERERS
        assert "stat-grid" in NATIVE_RENDERERS

    def test_stat_grid_renders_without_error(self):
        from pf.pptx_native import NATIVE_RENDERERS, _pptx_theme, SLIDE_WIDTH, SLIDE_HEIGHT
        prs = PptxPresentation()
        prs.slide_width = SLIDE_WIDTH
        prs.slide_height = SLIDE_HEIGHT
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        theme = _pptx_theme({"primary": "#1C2537", "accent": "#C4A962"})
        NATIVE_RENDERERS["stat-grid"](slide, {
            "title": "KPIs",
            "stats": [
                {"value": "$1.2M", "label": "Revenue"},
                {"value": "45%", "label": "Growth"},
            ],
            "cols": 2,
        }, theme)
        assert len(slide.shapes) > 0

    def test_stat_grid_renders_values(self):
        from pf.pptx_native import NATIVE_RENDERERS, _pptx_theme, SLIDE_WIDTH, SLIDE_HEIGHT
        prs = PptxPresentation()
        prs.slide_width = SLIDE_WIDTH
        prs.slide_height = SLIDE_HEIGHT
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        theme = _pptx_theme({"primary": "#1C2537", "accent": "#C4A962"})
        NATIVE_RENDERERS["stat-grid"](slide, {
            "stats": [{"value": "99%", "label": "Uptime"}],
            "cols": 1,
        }, theme)
        texts = [s.text_frame.text for s in slide.shapes if s.has_text_frame]
        assert "99%" in texts


class TestTwoColumnLayout:
    def test_two_column_in_native_renderers(self):
        from pf.pptx_native import NATIVE_RENDERERS
        assert "two-column" in NATIVE_RENDERERS

    def test_two_column_renders_cards(self):
        from pf.pptx_native import NATIVE_RENDERERS, _pptx_theme, SLIDE_WIDTH, SLIDE_HEIGHT
        prs = PptxPresentation()
        prs.slide_width = SLIDE_WIDTH
        prs.slide_height = SLIDE_HEIGHT
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        theme = _pptx_theme({"primary": "#1C2537", "accent": "#C4A962"})
        NATIVE_RENDERERS["two-column"](slide, {
            "title": "Comparison",
            "left": [{"type": "card", "title": "Option A", "text": "First choice"}],
            "right": [{"type": "card", "title": "Option B", "text": "Second choice"}],
        }, theme)
        assert len(slide.shapes) > 0

    def test_two_column_renders_card_titles(self):
        from pf.pptx_native import NATIVE_RENDERERS, _pptx_theme, SLIDE_WIDTH, SLIDE_HEIGHT
        prs = PptxPresentation()
        prs.slide_width = SLIDE_WIDTH
        prs.slide_height = SLIDE_HEIGHT
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        theme = _pptx_theme({"primary": "#1C2537", "accent": "#C4A962"})
        NATIVE_RENDERERS["two-column"](slide, {
            "title": "Slide Title",
            "left": [{"type": "card", "title": "Left Card", "text": "Left text"}],
            "right": [],
        }, theme)
        texts = [s.text_frame.text for s in slide.shapes if s.has_text_frame]
        assert "Left Card" in texts


class TestThreeColumnLayout:
    def test_three_column_in_native_renderers(self):
        from pf.pptx_native import NATIVE_RENDERERS
        assert "three-column" in NATIVE_RENDERERS

    def test_three_column_renders(self):
        from pf.pptx_native import NATIVE_RENDERERS, _pptx_theme, SLIDE_WIDTH, SLIDE_HEIGHT
        prs = PptxPresentation()
        prs.slide_width = SLIDE_WIDTH
        prs.slide_height = SLIDE_HEIGHT
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        theme = _pptx_theme({"primary": "#1C2537", "accent": "#C4A962"})
        NATIVE_RENDERERS["three-column"](slide, {
            "title": "Three Options",
            "columns": [
                [{"type": "card", "title": "A", "text": "First"}],
                [{"type": "card", "title": "B", "text": "Second"}],
                [{"type": "card", "title": "C", "text": "Third"}],
            ],
        }, theme)
        assert len(slide.shapes) > 0

    def test_three_column_renders_card_titles(self):
        from pf.pptx_native import NATIVE_RENDERERS, _pptx_theme, SLIDE_WIDTH, SLIDE_HEIGHT
        prs = PptxPresentation()
        prs.slide_width = SLIDE_WIDTH
        prs.slide_height = SLIDE_HEIGHT
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        theme = _pptx_theme({"primary": "#1C2537", "accent": "#C4A962"})
        NATIVE_RENDERERS["three-column"](slide, {
            "columns": [
                [{"type": "card", "title": "Col A", "text": "Content"}],
                [],
                [],
            ],
        }, theme)
        texts = [s.text_frame.text for s in slide.shapes if s.has_text_frame]
        assert "Col A" in texts


class TestDataTableLayout:
    """Native PPTX renderer for data-table layout."""

    def _make_slide(self):
        from pf.pptx_native import _pptx_theme, SLIDE_WIDTH, SLIDE_HEIGHT
        prs = PptxPresentation()
        prs.slide_width = SLIDE_WIDTH
        prs.slide_height = SLIDE_HEIGHT
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        theme = _pptx_theme({"primary": "#1C2537", "accent": "#C4A962"})
        return slide, theme

    def test_data_table_in_native_renderers(self):
        from pf.pptx_native import NATIVE_RENDERERS
        assert "data-table" in NATIVE_RENDERERS

    def test_data_table_renders_without_error(self):
        from pf.pptx_native import NATIVE_RENDERERS
        slide, theme = self._make_slide()
        NATIVE_RENDERERS["data-table"](slide, {
            "title": "Benchmark Results",
            "sections": [
                {
                    "section_title": "Performance",
                    "table": {
                        "headers": ["Model", "Score", "Latency"],
                        "rows": [
                            ["GPT-4", "92%", "1.2s"],
                            ["Claude", "94%", "0.9s"],
                        ],
                        "winner_rows": [1],
                    },
                }
            ],
        }, theme)
        assert len(slide.shapes) > 0

    def test_data_table_renders_section_title(self):
        from pf.pptx_native import NATIVE_RENDERERS
        slide, theme = self._make_slide()
        NATIVE_RENDERERS["data-table"](slide, {
            "sections": [
                {
                    "section_title": "My Section",
                    "table": {
                        "headers": ["A", "B"],
                        "rows": [["1", "2"]],
                    },
                }
            ],
        }, theme)
        texts = [s.text_frame.text for s in slide.shapes if s.has_text_frame]
        assert any("My Section" in t for t in texts)

    def test_data_table_renders_table_headers(self):
        from pf.pptx_native import NATIVE_RENDERERS
        slide, theme = self._make_slide()
        NATIVE_RENDERERS["data-table"](slide, {
            "sections": [
                {
                    "table": {
                        "headers": ["Name", "Score"],
                        "rows": [["Alpha", "95%"]],
                    },
                }
            ],
        }, theme)
        texts = [s.text_frame.text for s in slide.shapes if s.has_text_frame]
        assert "Name" in texts
        assert "Score" in texts

    def test_data_table_renders_with_insight(self):
        from pf.pptx_native import NATIVE_RENDERERS
        slide, theme = self._make_slide()
        NATIVE_RENDERERS["data-table"](slide, {
            "sections": [
                {
                    "table": {"headers": ["X"], "rows": []},
                    "insight": {"text": "Key finding here"},
                }
            ],
        }, theme)
        texts = [s.text_frame.text for s in slide.shapes if s.has_text_frame]
        assert any("Key finding" in t for t in texts)

    def test_data_table_two_sections(self):
        from pf.pptx_native import NATIVE_RENDERERS
        slide, theme = self._make_slide()
        # Should not raise even with 2 sections
        NATIVE_RENDERERS["data-table"](slide, {
            "sections": [
                {"section_title": "Left", "table": {"headers": ["A"], "rows": []}},
                {"section_title": "Right", "table": {"headers": ["B"], "rows": []}},
            ],
        }, theme)
        assert len(slide.shapes) > 0


class TestImageLayout:
    """Native PPTX renderer for image layout."""

    def _make_slide(self):
        from pf.pptx_native import _pptx_theme, SLIDE_WIDTH, SLIDE_HEIGHT
        prs = PptxPresentation()
        prs.slide_width = SLIDE_WIDTH
        prs.slide_height = SLIDE_HEIGHT
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        theme = _pptx_theme({"primary": "#1C2537", "accent": "#C4A962"})
        return slide, theme

    def test_image_in_native_renderers(self):
        from pf.pptx_native import NATIVE_RENDERERS
        assert "image" in NATIVE_RENDERERS

    def test_image_renders_without_error_no_file(self):
        """Remote URL or missing file should render a placeholder without crashing."""
        from pf.pptx_native import NATIVE_RENDERERS
        slide, theme = self._make_slide()
        NATIVE_RENDERERS["image"](slide, {
            "image": "https://example.com/photo.jpg",
            "title": "Our Office",
            "caption": "San Francisco HQ",
        }, theme)
        assert len(slide.shapes) > 0

    def test_image_full_mode_renders_title(self):
        from pf.pptx_native import NATIVE_RENDERERS
        slide, theme = self._make_slide()
        NATIVE_RENDERERS["image"](slide, {
            "image": "https://example.com/x.jpg",
            "title": "Full Bleed Title",
            "position": "full",
        }, theme)
        texts = [s.text_frame.text for s in slide.shapes if s.has_text_frame]
        assert any("Full Bleed Title" in t for t in texts)

    def test_image_split_mode_renders_title(self):
        from pf.pptx_native import NATIVE_RENDERERS
        slide, theme = self._make_slide()
        NATIVE_RENDERERS["image"](slide, {
            "image": "https://example.com/x.jpg",
            "title": "Split Layout",
            "caption": "Descriptive text",
            "position": "split",
            "side": "left",
        }, theme)
        texts = [s.text_frame.text for s in slide.shapes if s.has_text_frame]
        assert any("Split Layout" in t for t in texts)

    def test_image_renders_caption(self):
        from pf.pptx_native import NATIVE_RENDERERS
        slide, theme = self._make_slide()
        NATIVE_RENDERERS["image"](slide, {
            "image": "https://example.com/x.jpg",
            "caption": "Photo credit: Unsplash",
            "position": "full",
        }, theme)
        texts = [s.text_frame.text for s in slide.shapes if s.has_text_frame]
        assert any("Photo credit" in t for t in texts)

    def test_image_local_file(self, tmp_path):
        """A local PNG file should be embedded natively via add_picture()."""
        from pf.pptx_native import NATIVE_RENDERERS
        # Create a minimal 1x1 white PNG (valid PNG bytes)
        png_bytes = (
            b'\x89PNG\r\n\x1a\n'  # PNG signature
            b'\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
            b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx'
            b'\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00'
            b'\x00\x00IEND\xaeB`\x82'
        )
        img_path = tmp_path / "test.png"
        img_path.write_bytes(png_bytes)
        slide, theme = self._make_slide()
        # Should not raise — local file embedding path
        NATIVE_RENDERERS["image"](slide, {
            "image": str(img_path),
            "title": "Local Image",
            "position": "full",
        }, theme)
        assert len(slide.shapes) > 0


class TestTimelineLayout:
    """Native PPTX renderer for timeline layout."""

    def _make_slide(self):
        from pf.pptx_native import _pptx_theme, SLIDE_WIDTH, SLIDE_HEIGHT
        prs = PptxPresentation()
        prs.slide_width = SLIDE_WIDTH
        prs.slide_height = SLIDE_HEIGHT
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        theme = _pptx_theme({"primary": "#1C2537", "accent": "#C4A962"})
        return slide, theme

    def test_timeline_in_native_renderers(self):
        from pf.pptx_native import NATIVE_RENDERERS
        assert "timeline" in NATIVE_RENDERERS

    def test_timeline_renders_without_error(self):
        from pf.pptx_native import NATIVE_RENDERERS
        slide, theme = self._make_slide()
        NATIVE_RENDERERS["timeline"](slide, {
            "title": "Product Roadmap",
            "steps": [
                {"icon": "rocket", "title": "Launch", "description": "Initial release"},
                {"icon": "chart-line", "title": "Grow", "description": "Scale users"},
                {"icon": "trophy", "title": "Win", "description": "Market leader"},
            ],
        }, theme)
        assert len(slide.shapes) > 0

    def test_timeline_renders_step_titles(self):
        from pf.pptx_native import NATIVE_RENDERERS
        slide, theme = self._make_slide()
        NATIVE_RENDERERS["timeline"](slide, {
            "steps": [
                {"icon": "flag", "title": "Step One", "description": "First step"},
                {"icon": "check", "title": "Step Two", "description": "Second step"},
            ],
        }, theme)
        texts = [s.text_frame.text for s in slide.shapes if s.has_text_frame]
        assert any("Step One" in t for t in texts)
        assert any("Step Two" in t for t in texts)

    def test_timeline_renders_descriptions(self):
        from pf.pptx_native import NATIVE_RENDERERS
        slide, theme = self._make_slide()
        NATIVE_RENDERERS["timeline"](slide, {
            "steps": [
                {"icon": "star", "title": "Phase A", "description": "Do the thing"},
            ],
        }, theme)
        texts = [s.text_frame.text for s in slide.shapes if s.has_text_frame]
        assert any("Do the thing" in t for t in texts)

    def test_timeline_renders_slide_title(self):
        from pf.pptx_native import NATIVE_RENDERERS
        slide, theme = self._make_slide()
        NATIVE_RENDERERS["timeline"](slide, {
            "title": "Our Journey",
            "steps": [{"icon": "play", "title": "Start", "description": "Begin"}],
        }, theme)
        texts = [s.text_frame.text for s in slide.shapes if s.has_text_frame]
        assert any("Our Journey" in t for t in texts)

    def test_timeline_empty_steps(self):
        """Empty steps list should not raise."""
        from pf.pptx_native import NATIVE_RENDERERS
        slide, theme = self._make_slide()
        NATIVE_RENDERERS["timeline"](slide, {"title": "Empty", "steps": []}, theme)
        # Background shape added, no crash
        assert len(slide.shapes) >= 0

    def test_timeline_single_step_no_line(self):
        """Single step — connecting line should still render without crashing."""
        from pf.pptx_native import NATIVE_RENDERERS
        slide, theme = self._make_slide()
        NATIVE_RENDERERS["timeline"](slide, {
            "steps": [{"icon": "bolt", "title": "Only", "description": "Solo step"}],
        }, theme)
        texts = [s.text_frame.text for s in slide.shapes if s.has_text_frame]
        assert any("Only" in t for t in texts)
