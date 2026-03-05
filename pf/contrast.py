"""
ContrastChecker — WCAG 2.1 color contrast analysis for build-time warnings.

Computes relative luminance and contrast ratios to flag text/accent combinations
that may be hard to read on slides.
"""


def _linearize(channel: float) -> float:
    """Convert sRGB channel (0-1) to linear RGB."""
    if channel <= 0.04045:
        return channel / 12.92
    return ((channel + 0.055) / 1.055) ** 2.4


def relative_luminance(hex_color: str) -> float:
    """Compute WCAG 2.1 relative luminance from a hex color string.

    Returns a value between 0.0 (black) and 1.0 (white).
    Formula: L = 0.2126 * R + 0.7152 * G + 0.0722 * B
    """
    h = hex_color.lstrip("#")
    r = _linearize(int(h[0:2], 16) / 255)
    g = _linearize(int(h[2:4], 16) / 255)
    b = _linearize(int(h[4:6], 16) / 255)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(color1: str, color2: str) -> float:
    """Compute WCAG 2.1 contrast ratio between two hex colors.

    Returns a value between 1.0 (identical) and 21.0 (black/white).
    """
    l1 = relative_luminance(color1)
    l2 = relative_luminance(color2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return round((lighter + 0.05) / (darker + 0.05), 1)


# Text colors hardcoded in generate_variables_css
_TEXT_COLORS = {
    "text (#e0e0e0)": "#e0e0e0",
    "text-light (#cccccc)": "#cccccc",
    "text-muted (#aaaaaa)": "#aaaaaa",
}

# Minimum contrast ratios (WCAG 2.1 AA)
_MIN_TEXT_RATIO = 4.5       # Normal text
_MIN_LARGE_TEXT_RATIO = 3.0  # Large text (18pt+ / 14pt+ bold)


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
        ratio = contrast_ratio(color, primary)
        threshold = _MIN_TEXT_RATIO if "muted" not in name else _MIN_LARGE_TEXT_RATIO
        if ratio < threshold:
            warnings.append(
                f"{name} on primary ({primary}): contrast {ratio}:1 "
                f"(need {threshold}:1 for WCAG AA)"
            )

    # Accent on primary (used at large sizes — headers, stats)
    accent_ratio = contrast_ratio(accent, primary)
    if accent_ratio < _MIN_LARGE_TEXT_RATIO:
        warnings.append(
            f"accent ({accent}) on primary ({primary}): contrast {accent_ratio}:1 "
            f"(need {_MIN_LARGE_TEXT_RATIO}:1 for WCAG AA large text)"
        )

    # Secondary accent on primary
    if secondary_accent:
        sec_ratio = contrast_ratio(secondary_accent, primary)
        if sec_ratio < _MIN_LARGE_TEXT_RATIO:
            warnings.append(
                f"secondary_accent ({secondary_accent}) on primary ({primary}): "
                f"contrast {sec_ratio}:1 "
                f"(need {_MIN_LARGE_TEXT_RATIO}:1 for WCAG AA large text)"
            )

    return warnings
