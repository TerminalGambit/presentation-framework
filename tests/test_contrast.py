"""Tests for WCAG contrast ratio calculations."""

import pytest

from pf.contrast import (
    relative_luminance,
    contrast_ratio,
    _raw_contrast_ratio,
    check_contrast,
)


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

    def test_rounding_does_not_mask_failing_ratio(self):
        """A raw ratio just below 3.0 that rounds to 3.0 should still warn.

        #0070f0 on #2e2e2e has raw ratio ~2.959 which rounds to 3.0,
        but must fail the 3.0:1 large-text threshold.
        """
        # Verify our assumption: rounded looks passing, raw is below
        assert contrast_ratio("#0070f0", "#2e2e2e") == 3.0
        assert _raw_contrast_ratio("#0070f0", "#2e2e2e") < 3.0

        warnings = check_contrast(primary="#2e2e2e", accent="#0070f0")
        assert any("accent" in w for w in warnings)

    def test_accent_too_similar_to_text_warns(self):
        """Accent indistinguishable from body text should warn."""
        warnings = check_contrast(
            primary="#1C2537",
            accent="#d5d5d5",  # Very close to text color #e0e0e0
        )
        assert any("distinguishability" in w for w in warnings)

    def test_accent_distinct_from_text_no_warn(self):
        """A clearly distinct accent should not trigger the text warning."""
        warnings = check_contrast(
            primary="#1C2537",
            accent="#C4A962",
        )
        assert not any("distinguishability" in w for w in warnings)


class TestHexValidation:
    def test_3char_hex(self):
        """3-char shorthand #fff should expand to #ffffff."""
        assert relative_luminance("#fff") == 1.0

    def test_3char_hex_color(self):
        """3-char shorthand should expand each char: #abc → #aabbcc."""
        assert relative_luminance("#abc") == relative_luminance("#aabbcc")

    def test_invalid_hex_raises(self):
        """Non-hex strings should raise ValueError."""
        with pytest.raises(ValueError, match="Invalid hex color"):
            relative_luminance("not-a-color")

    def test_too_short_hex_raises(self):
        """A 2-char hex is invalid."""
        with pytest.raises(ValueError, match="Invalid hex color"):
            relative_luminance("#ab")

    def test_too_long_hex_raises(self):
        """A 7-char hex is invalid."""
        with pytest.raises(ValueError, match="Invalid hex color"):
            relative_luminance("#1234567")
