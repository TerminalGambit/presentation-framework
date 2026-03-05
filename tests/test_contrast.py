"""Tests for WCAG contrast ratio calculations."""

from pf.contrast import relative_luminance, contrast_ratio, check_contrast


class TestRelativeLuminance:
    def test_black(self):
        assert relative_luminance("#000000") == 0.0

    def test_white(self):
        assert relative_luminance("#ffffff") == 1.0

    def test_mid_gray(self):
        lum = relative_luminance("#808080")
        assert 0.2 < lum < 0.25  # ~0.2159

    def test_red(self):
        lum = relative_luminance("#ff0000")
        assert 0.2 < lum < 0.22  # ~0.2126


class TestContrastRatio:
    def test_black_on_white(self):
        ratio = contrast_ratio("#000000", "#ffffff")
        assert ratio == 21.0

    def test_white_on_black(self):
        """Order should not matter."""
        ratio = contrast_ratio("#ffffff", "#000000")
        assert ratio == 21.0

    def test_same_color(self):
        ratio = contrast_ratio("#336699", "#336699")
        assert ratio == 1.0

    def test_known_pair(self):
        """Dark blue bg with light gray text — should be high contrast."""
        ratio = contrast_ratio("#e0e0e0", "#1C2537")
        assert ratio > 10  # Very readable


class TestCheckContrast:
    def test_good_contrast_no_warnings(self):
        """Default dark theme with light text should pass."""
        warnings = check_contrast(
            primary="#1C2537",
            accent="#C4A962",
            secondary_accent="#5B8FA8",
        )
        assert len(warnings) == 0

    def test_low_contrast_accent_warns(self):
        """An accent too close to the background should warn."""
        warnings = check_contrast(
            primary="#1C2537",
            accent="#1A2030",  # Almost identical to primary
        )
        assert len(warnings) > 0
        assert any("accent" in w.lower() for w in warnings)

    def test_low_contrast_text_warns(self):
        """A very light primary makes default text hard to read."""
        warnings = check_contrast(
            primary="#F0F0F0",  # Light bg, but text is also light (#e0e0e0)
            accent="#C4A962",
        )
        assert len(warnings) > 0
