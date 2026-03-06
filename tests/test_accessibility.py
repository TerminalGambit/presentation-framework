"""Tests for pf.accessibility — accessibility auditing module."""

import os
from pathlib import Path

import pytest

from pf.accessibility import (
    AccessibilityWarning,
    check_accessibility,
    check_slide_dir,
    generate_alt_text,
)
from pf.builder import PresentationBuilder


# ── check_accessibility — img alt text ─────────────────────────────────────

class TestMissingAlt:
    def test_warns_missing_alt(self):
        """An <img> without an alt attribute should produce an error."""
        html = "<html><body><img src='photo.jpg'></body></html>"
        warnings = check_accessibility(html, "test.html")
        img_warnings = [w for w in warnings if "alt" in w.issue]
        assert len(img_warnings) >= 1
        assert img_warnings[0].severity == "error"

    def test_no_warning_when_alt_present(self):
        """An <img> with alt='' or alt='text' should NOT produce an alt warning."""
        html = "<html><body><img src='photo.jpg' alt='A photo'></body></html>"
        warnings = check_accessibility(html, "test.html")
        img_warnings = [w for w in warnings if "alt" in w.issue]
        assert len(img_warnings) == 0

    def test_no_warning_when_empty_alt_present(self):
        """An <img> with empty alt='' (decorative image) should NOT produce an alt warning."""
        html = "<html><body><img src='decorative.jpg' alt=''></body></html>"
        warnings = check_accessibility(html, "test.html")
        img_warnings = [w for w in warnings if "alt" in w.issue]
        assert len(img_warnings) == 0

    def test_error_contains_filename(self):
        """The suggestion should contain the filename-derived alt text."""
        html = "<img src='images/team-photo.jpg'>"
        warnings = check_accessibility(html, "slide_01.html")
        img_warnings = [w for w in warnings if "alt" in w.issue]
        assert len(img_warnings) >= 1
        assert "Team Photo" in img_warnings[0].suggestion

    def test_errors_sorted_first(self):
        """Errors should appear before warnings in the returned list."""
        html = "<img src='photo.jpg'><button></button>"
        warnings = check_accessibility(html, "test.html")
        if len(warnings) >= 2:
            severities = [w.severity for w in warnings]
            error_idx = severities.index("error") if "error" in severities else -1
            warning_idx = severities.index("warning") if "warning" in severities else -1
            if error_idx >= 0 and warning_idx >= 0:
                assert error_idx <= warning_idx


# ── check_accessibility — aria-label on interactive elements ───────────────

class TestMissingAria:
    def test_warns_missing_aria_button(self):
        """A <button> without aria-label and no visible text should warn."""
        html = "<html><body><button></button></body></html>"
        warnings = check_accessibility(html, "test.html")
        aria_warnings = [w for w in warnings if "aria-label" in w.issue or "button" in w.issue]
        assert len(aria_warnings) >= 1
        assert aria_warnings[0].severity == "warning"

    def test_no_aria_warning_with_text(self):
        """A <button> with visible text should NOT produce an aria warning."""
        html = "<html><body><button>Click me</button></body></html>"
        warnings = check_accessibility(html, "test.html")
        aria_warnings = [
            w for w in warnings
            if "aria-label" in w.issue and "button" in w.issue
        ]
        assert len(aria_warnings) == 0

    def test_no_aria_warning_when_aria_label_present(self):
        """A <button> with aria-label should NOT produce an aria warning."""
        html = '<html><body><button aria-label="Close dialog"></button></body></html>'
        warnings = check_accessibility(html, "test.html")
        aria_warnings = [
            w for w in warnings
            if "aria-label" in w.issue and "button" in w.issue
        ]
        assert len(aria_warnings) == 0

    def test_warns_missing_aria_input(self):
        """An <input> without aria-label should warn."""
        html = '<html><body><input type="text"></body></html>'
        warnings = check_accessibility(html, "test.html")
        aria_warnings = [w for w in warnings if "input" in w.issue]
        assert len(aria_warnings) >= 1


# ── generate_alt_text ───────────────────────────────────────────────────────

class TestGenerateAltText:
    def test_hyphenated_filename(self):
        assert generate_alt_text("images/team-photo.jpg") == "Team Photo"

    def test_underscored_filename(self):
        assert generate_alt_text("quarterly_revenue.png") == "Quarterly Revenue"

    def test_simple_filename(self):
        assert generate_alt_text("logo.svg") == "Logo"

    def test_deeply_nested_path(self):
        assert generate_alt_text("/path/to/my-image.jpg") == "My Image"

    def test_url_src(self):
        assert generate_alt_text("https://example.com/hero-banner.png") == "Hero Banner"

    def test_complex_filename(self):
        assert generate_alt_text("images/quarterly-revenue-chart.png") == "Quarterly Revenue Chart"

    def test_filename_with_multiple_separators(self):
        result = generate_alt_text("my_great-logo.png")
        assert result == "My Great Logo"


# ── check_slide_dir ─────────────────────────────────────────────────────────

class TestCheckSlideDir:
    def test_check_slide_dir(self, tmp_path):
        """Warnings only from slide_01 (missing alt), not slide_02 (clean)."""
        slide01 = tmp_path / "slide_01.html"
        slide01.write_text(
            "<html><body><img src='photo.jpg'></body></html>",
            encoding="utf-8",
        )
        slide02 = tmp_path / "slide_02.html"
        slide02.write_text(
            "<html><body><p>Clean slide with role</p><div role='region' aria-label='x'></div></body></html>",
            encoding="utf-8",
        )

        warnings = check_slide_dir(str(tmp_path))
        filenames = {w.file for w in warnings}
        assert "slide_01.html" in filenames
        # slide_02 has no img issues
        assert not any(w.file == "slide_02.html" and "alt" in w.issue for w in warnings)

    def test_check_slide_dir_ignores_non_slides(self, tmp_path):
        """Non-slide files (present.html etc.) should be ignored."""
        (tmp_path / "present.html").write_text("<img src='x.jpg'>", encoding="utf-8")
        (tmp_path / "index.html").write_text("<img src='y.jpg'>", encoding="utf-8")
        (tmp_path / "slide_01.html").write_text(
            "<img src='z.jpg' alt='Z'>", encoding="utf-8"
        )

        warnings = check_slide_dir(str(tmp_path))
        filenames = {w.file for w in warnings}
        assert "present.html" not in filenames
        assert "index.html" not in filenames

    def test_check_slide_dir_nonexistent(self, tmp_path):
        """Missing directory should return empty list, not crash."""
        warnings = check_slide_dir(str(tmp_path / "nonexistent"))
        assert warnings == []


# ── AccessibilityWarning dataclass ──────────────────────────────────────────

class TestAccessibilityWarningDataclass:
    def test_all_fields_accessible(self):
        w = AccessibilityWarning(
            file="slide_01.html",
            element="<img src='x.jpg'>",
            issue="missing alt attribute",
            suggestion="Add alt='X'",
            severity="error",
        )
        assert w.file == "slide_01.html"
        assert w.element == "<img src='x.jpg'>"
        assert w.issue == "missing alt attribute"
        assert w.suggestion == "Add alt='X'"
        assert w.severity == "error"

    def test_warning_severity(self):
        w = AccessibilityWarning(
            file="slide.html",
            element="<button>",
            issue="missing aria-label",
            suggestion="Add aria-label",
            severity="warning",
        )
        assert w.severity == "warning"


# ── Base template ARIA attributes ───────────────────────────────────────────

class TestBaseTemplateAria:
    @pytest.fixture
    def builder(self):
        b = PresentationBuilder()
        b.config = {
            "meta": {"title": "Test Deck"},
            "theme": {
                "fonts": {
                    "heading": "Playfair Display",
                    "subheading": "Montserrat",
                    "body": "Lato",
                }
            },
        }
        return b

    def test_base_template_has_role_region(self, builder):
        """Built HTML should contain role='region' on the slide container."""
        slide = {"layout": "section", "data": {"title": "Test Section"}}
        html = builder.render_slide(slide, 0)
        assert 'role="region"' in html

    def test_base_template_has_aria_label(self, builder):
        """Built HTML should contain aria-label on the slide container."""
        slide = {"layout": "section", "data": {"title": "Test Section"}}
        html = builder.render_slide(slide, 0)
        assert "aria-label=" in html

    def test_base_template_has_tabindex(self, builder):
        """Built HTML should contain tabindex='0' on the slide container."""
        slide = {"layout": "section", "data": {"title": "Test Section"}}
        html = builder.render_slide(slide, 0)
        assert 'tabindex="0"' in html


# ── High-contrast CSS exists ────────────────────────────────────────────────

class TestHighContrastCSS:
    BASE_CSS = Path(__file__).parent.parent / "theme" / "base.css"

    def test_high_contrast_class_exists(self):
        """theme/base.css must contain .pf-high-contrast."""
        css = self.BASE_CSS.read_text(encoding="utf-8")
        assert ".pf-high-contrast" in css

    def test_high_contrast_overrides_primary(self):
        """High-contrast mode should override --pf-primary to black."""
        css = self.BASE_CSS.read_text(encoding="utf-8")
        assert "--pf-primary: #000000" in css

    def test_high_contrast_accent_is_gold(self):
        """High-contrast mode should use gold (#FFD700) as accent for WCAG AAA."""
        css = self.BASE_CSS.read_text(encoding="utf-8")
        assert "--pf-accent: #FFD700" in css


# ── High-contrast toggle in template ────────────────────────────────────────

class TestHighContrastToggleInTemplate:
    TEMPLATE = Path(__file__).parent.parent / "templates" / "base.html.j2"

    def test_toggle_button_class_exists(self):
        """Template must have the .pf-hc-toggle button class."""
        template = self.TEMPLATE.read_text(encoding="utf-8")
        assert "pf-hc-toggle" in template

    def test_classlist_toggle_pf_high_contrast(self):
        """Template JS must call classList.toggle with pf-high-contrast."""
        template = self.TEMPLATE.read_text(encoding="utf-8")
        assert "classList.toggle" in template
        assert "pf-high-contrast" in template

    def test_keyboard_shortcut_h(self):
        """Template JS must handle 'h' and 'H' keydown for high-contrast toggle."""
        template = self.TEMPLATE.read_text(encoding="utf-8")
        assert "keydown" in template
        # The JS references 'h' or 'H' keys
        assert "'h'" in template or "'H'" in template

    def test_toggle_button_has_aria_label(self):
        """The toggle button must have an aria-label for accessibility."""
        template = self.TEMPLATE.read_text(encoding="utf-8")
        assert 'aria-label="Toggle high-contrast mode"' in template
