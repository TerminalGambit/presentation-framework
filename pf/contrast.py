"""
ContrastChecker — WCAG 2.1 color contrast analysis for build-time warnings.

Computes relative luminance and contrast ratios to flag text/accent combinations
that may be hard to read on slides.
"""

import re

_HEX_RE = re.compile(r"^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


def _linearize(channel: float) -> float:
    """Convert sRGB channel (0-1) to linear RGB."""
    if channel <= 0.04045:
        return channel / 12.92
    return ((channel + 0.055) / 1.055) ** 2.4


def relative_luminance(hex_color: str) -> float:
    """Compute WCAG 2.1 relative luminance from a hex color string.

    Accepts 3-char shorthand (#fff → #ffffff) and optional leading '#'.
    Raises ValueError for malformed hex strings.

    Returns a value between 0.0 (black) and 1.0 (white).
    Formula: L = 0.2126 * R + 0.7152 * G + 0.0722 * B
    """
    if not _HEX_RE.match(hex_color):
        raise ValueError(
            f"Invalid hex color '{hex_color}': expected format #RRGGBB or #RGB"
        )
    h = hex_color.lstrip("#")
    # Expand 3-char shorthand: #abc → #aabbcc
    if len(h) == 3:
        h = h[0] * 2 + h[1] * 2 + h[2] * 2
    r = _linearize(int(h[0:2], 16) / 255)
    g = _linearize(int(h[2:4], 16) / 255)
    b = _linearize(int(h[4:6], 16) / 255)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _raw_contrast_ratio(color1: str, color2: str) -> float:
    """Compute unrounded WCAG 2.1 contrast ratio between two hex colors.

    Used internally for threshold comparisons where rounding could mask
    a failing ratio (e.g. 2.96 rounding to 3.0).
    """
    l1 = relative_luminance(color1)
    l2 = relative_luminance(color2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def contrast_ratio(color1: str, color2: str) -> float:
    """Compute WCAG 2.1 contrast ratio between two hex colors (rounded for display).

    Returns a value between 1.0 (identical) and 21.0 (black/white),
    rounded to 1 decimal place.
    """
    return round(_raw_contrast_ratio(color1, color2), 1)


# Text colors hardcoded in generate_variables_css
_TEXT_COLORS = {
    "text (#e0e0e0)": "#e0e0e0",
    "text-light (#cccccc)": "#cccccc",
    "text-muted (#aaaaaa)": "#aaaaaa",
}

# Minimum contrast ratios (WCAG 2.1 AA)
_MIN_TEXT_RATIO = 4.5         # Normal text
_MIN_LARGE_TEXT_RATIO = 3.0   # Large text (18pt+ / 14pt+ bold)
_MIN_ACCENT_TEXT_RATIO = 1.5  # Accent vs body text distinguishability


def check_contrast(
    primary: str,
    accent: str,
    secondary_accent: str | None = None,
) -> list[str]:
    """Check key color pairs against WCAG AA thresholds.

    Returns a list of warning strings (empty if all pairs pass).
    """
    warnings = []

    # Text colors on primary background
    for name, color in _TEXT_COLORS.items():
        raw = _raw_contrast_ratio(color, primary)
        threshold = _MIN_TEXT_RATIO if "muted" not in name else _MIN_LARGE_TEXT_RATIO
        if raw < threshold:
            display = contrast_ratio(color, primary)
            warnings.append(
                f"{name} on primary ({primary}): contrast {display}:1 "
                f"(need {threshold}:1 for WCAG AA)"
            )

    # Accent on primary (used at large sizes — headers, stats)
    raw_accent = _raw_contrast_ratio(accent, primary)
    if raw_accent < _MIN_LARGE_TEXT_RATIO:
        display_accent = contrast_ratio(accent, primary)
        warnings.append(
            f"accent ({accent}) on primary ({primary}): contrast {display_accent}:1 "
            f"(need {_MIN_LARGE_TEXT_RATIO}:1 for WCAG AA large text)"
        )

    # Accent vs body text — distinguishability check
    raw_accent_text = _raw_contrast_ratio(accent, "#e0e0e0")
    if raw_accent_text < _MIN_ACCENT_TEXT_RATIO:
        display_accent_text = contrast_ratio(accent, "#e0e0e0")
        warnings.append(
            f"accent ({accent}) vs text (#e0e0e0): contrast {display_accent_text}:1 "
            f"(need {_MIN_ACCENT_TEXT_RATIO}:1 for distinguishability)"
        )

    # Secondary accent on primary
    if secondary_accent:
        raw_sec = _raw_contrast_ratio(secondary_accent, primary)
        if raw_sec < _MIN_LARGE_TEXT_RATIO:
            display_sec = contrast_ratio(secondary_accent, primary)
            warnings.append(
                f"secondary_accent ({secondary_accent}) on primary ({primary}): "
                f"contrast {display_sec}:1 "
                f"(need {_MIN_LARGE_TEXT_RATIO}:1 for WCAG AA large text)"
            )

    return warnings
