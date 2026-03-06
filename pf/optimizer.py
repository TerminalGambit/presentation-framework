"""
Slide content optimizer — splits overflowing slides into non-overflowing ones.

Provides split_slide() which uses LayoutAnalyzer height estimates to redistribute
content blocks across multiple slides when a single slide would overflow.
"""

import copy

from pf.analyzer import COLUMNAR_LAYOUTS, COLUMN_GAP, USABLE_HEIGHT, LayoutAnalyzer


def split_slide(slide: dict) -> list[dict]:
    """Take a slide dict and return a list of 1+ slide dicts that each fit within USABLE_HEIGHT.

    If the slide does not overflow or is not a columnar layout, returns [slide] unchanged.
    If the slide overflows, distributes content blocks across multiple slides so each fits.
    The continuation slide has '(cont.)' appended to its subtitle.
    Original slide dict is never mutated.
    """
    layout = slide.get("layout", "")

    # Non-columnar layouts pass through unchanged
    if layout not in COLUMNAR_LAYOUTS:
        return [slide]

    # No overflow — pass through unchanged
    if LayoutAnalyzer.analyze_slide(slide, 0) is None:
        return [slide]

    if layout == "two-column":
        return _split_two_column(slide)
    elif layout == "three-column":
        return _split_three_column(slide)
    elif layout == "data-table":
        return _split_data_table(slide)
    elif layout == "stat-grid":
        return _split_stat_grid(slide)

    # Fallback: return as-is (shouldn't happen for known columnar layouts)
    return [slide]


# ---------------------------------------------------------------------------
# Layout-specific splitters
# ---------------------------------------------------------------------------


def _split_two_column(slide: dict) -> list[dict]:
    """Split a two-column slide into two slides by redistributing left/right blocks."""
    data = slide.get("data", {})
    left = data.get("left", [])
    right = data.get("right", [])

    left_a, left_b = _fit_split(left)
    right_a, right_b = _fit_split(right)

    slide_a = copy.deepcopy(slide)
    slide_a["data"]["left"] = left_a
    slide_a["data"]["right"] = right_a

    slide_b = copy.deepcopy(slide)
    slide_b["data"]["left"] = left_b
    slide_b["data"]["right"] = right_b
    _set_continuation_subtitle(slide_b)

    results = []
    if _has_content(slide_a):
        results.append(slide_a)
    if _has_content(slide_b):
        results.append(slide_b)

    return results if results else [slide]


def _split_three_column(slide: dict) -> list[dict]:
    """Split a three-column slide into two slides by redistributing column blocks."""
    data = slide.get("data", {})
    columns = data.get("columns", [[], [], []])

    cols_a = []
    cols_b = []
    for col in columns:
        a, b = _fit_split(col)
        cols_a.append(a)
        cols_b.append(b)

    slide_a = copy.deepcopy(slide)
    slide_a["data"]["columns"] = cols_a

    slide_b = copy.deepcopy(slide)
    slide_b["data"]["columns"] = cols_b
    _set_continuation_subtitle(slide_b)

    results = []
    if _has_content(slide_a):
        results.append(slide_a)
    if _has_content(slide_b):
        results.append(slide_b)

    return results if results else [slide]


def _split_data_table(slide: dict) -> list[dict]:
    """Split a data-table slide into two slides by splitting sections."""
    data = slide.get("data", {})
    sections = data.get("sections", [])

    # Split at the section level: find how many sections fit in USABLE_HEIGHT
    accumulated = 0
    split_idx = len(sections)  # default: all sections fit (shouldn't happen since overflowing)

    for i, section in enumerate(sections):
        # Treat each section as a single-item block for height estimation
        section_block = section if isinstance(section, dict) else {}
        height = LayoutAnalyzer.estimate_block_height(section_block)
        gap = COLUMN_GAP if i > 0 else 0

        if i > 0 and accumulated + gap + height > USABLE_HEIGHT:
            split_idx = i
            break
        accumulated += gap + height

    # If the first section alone exceeds USABLE_HEIGHT, don't split into empty+content
    if split_idx == 0:
        return [slide]

    sections_a = sections[:split_idx]
    sections_b = sections[split_idx:]

    slide_a = copy.deepcopy(slide)
    slide_a["data"]["sections"] = sections_a

    slide_b = copy.deepcopy(slide)
    slide_b["data"]["sections"] = sections_b
    _set_continuation_subtitle(slide_b)

    results = []
    if sections_a:
        results.append(slide_a)
    if sections_b:
        results.append(slide_b)

    return results if results else [slide]


def _split_stat_grid(slide: dict) -> list[dict]:
    """Split a stat-grid slide by treating columns like two-column layout."""
    data = slide.get("data", {})
    columns = data.get("columns", [[], []])

    cols_a = []
    cols_b = []
    for col in columns:
        a, b = _fit_split(col)
        cols_a.append(a)
        cols_b.append(b)

    slide_a = copy.deepcopy(slide)
    slide_a["data"]["columns"] = cols_a

    slide_b = copy.deepcopy(slide)
    slide_b["data"]["columns"] = cols_b
    _set_continuation_subtitle(slide_b)

    results = []
    if _has_content(slide_a):
        results.append(slide_a)
    if _has_content(slide_b):
        results.append(slide_b)

    return results if results else [slide]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fit_split(blocks: list[dict]) -> tuple[list[dict], list[dict]]:
    """Return (fits, remainder) where fits is the longest prefix that stays within USABLE_HEIGHT.

    If the first block alone exceeds USABLE_HEIGHT, returns (blocks, []) to avoid
    producing an empty slide — the oversized block is emitted as-is.
    """
    if not blocks:
        return [], []

    accumulated = 0
    for i, block in enumerate(blocks):
        height = LayoutAnalyzer.estimate_block_height(block)
        gap = COLUMN_GAP if i > 0 else 0

        if i == 0:
            # First block: always include it even if oversized
            accumulated = height
        else:
            if accumulated + gap + height > USABLE_HEIGHT:
                # Split here
                return blocks[:i], blocks[i:]
            accumulated += gap + height

    # All blocks fit
    return blocks, []


def _has_content(slide: dict) -> bool:
    """Return True if the slide has at least one non-empty column/section in data."""
    data = slide.get("data", {})

    # two-column
    if data.get("left") or data.get("right"):
        return True

    # three-column, stat-grid (columns list)
    columns = data.get("columns", [])
    if any(col for col in columns):
        return True

    # data-table
    sections = data.get("sections", [])
    if sections:
        return True

    return False


def _set_continuation_subtitle(slide: dict) -> None:
    """Append '(cont.)' to the slide subtitle in-place, or set it to '(cont.)' if absent."""
    data = slide.get("data", {})
    existing = data.get("subtitle", "")
    if existing:
        data["subtitle"] = f"{existing} (cont.)"
    else:
        data["subtitle"] = "(cont.)"
