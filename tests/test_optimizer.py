"""Tests for pf.optimizer — split_slide() slide content optimizer."""

import copy

import pytest

from pf.optimizer import _fit_split, split_slide


# ---------------------------------------------------------------------------
# Helpers to build test slide dicts
# ---------------------------------------------------------------------------


def make_card(i: int, bullets: int = 3) -> dict:
    """Build a card block with a given number of bullets.

    With 3 bullets: 60 + 3*22 = 126px each.
    """
    return {
        "type": "card",
        "title": f"Card {i}",
        "text": "Description text",
        "bullets": [f"bullet {j}" for j in range(bullets)],
    }


def make_two_column_slide(left_count: int = 0, right_count: int = 0, bullets: int = 3) -> dict:
    """Build a two-column slide with card blocks."""
    return {
        "layout": "two-column",
        "data": {
            "title": "Test Slide",
            "subtitle": "A subtitle",
            "left": [make_card(i, bullets) for i in range(left_count)],
            "right": [make_card(i, bullets) for i in range(right_count)],
        },
    }


def make_three_column_slide(per_col: int = 0, bullets: int = 3) -> dict:
    """Build a three-column slide with card blocks in each column."""
    return {
        "layout": "three-column",
        "data": {
            "title": "Three Col Slide",
            "columns": [
                [make_card(i, bullets) for i in range(per_col)],
                [make_card(i, bullets) for i in range(per_col)],
                [make_card(i, bullets) for i in range(per_col)],
            ],
        },
    }


def make_data_table_slide(section_count: int = 1, rows_per_section: int = 20) -> dict:
    """Build a data-table slide. Each section with 20 rows is 725px > 575px USABLE_HEIGHT."""
    sections = [
        {
            "type": "table",
            "section_title": f"Section {i}",
            "headers": ["Name", "Value"],
            "rows": [[f"row {j}", str(j)] for j in range(rows_per_section)],
        }
        for i in range(section_count)
    ]
    return {
        "layout": "data-table",
        "data": {
            "title": "Data Table Slide",
            "sections": sections,
        },
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_split_two_column():
    """Two-column slide with 8 card blocks in the left column should split into 2 slides."""
    slide = make_two_column_slide(left_count=8, right_count=0, bullets=3)
    result = split_slide(slide)

    assert len(result) == 2
    for s in result:
        assert s["layout"] == "two-column"
    # Both resulting slides should have non-empty left columns
    assert len(result[0]["data"]["left"]) > 0
    assert len(result[1]["data"]["left"]) > 0


def test_split_single_overflow_no_empty():
    """A slide with a single oversized block should not produce an empty continuation slide."""
    # card with 50 bullets: 60 + 50*22 = 1160px >> 575px
    huge_card = make_card(0, bullets=50)
    slide = {
        "layout": "two-column",
        "data": {
            "title": "Single Huge Block",
            "left": [huge_card],
            "right": [],
        },
    }
    result = split_slide(slide)

    # Should produce exactly 1 slide (the oversized block, not empty+original)
    assert len(result) == 1


def test_no_split_when_fits():
    """A slide with content that fits within USABLE_HEIGHT is returned as-is."""
    # 2 small cards: 2 * insight(45) + 10 gap = 100px — well within 575px
    slide = {
        "layout": "two-column",
        "data": {
            "title": "Small Slide",
            "left": [
                {"type": "insight", "text": "First insight"},
                {"type": "insight", "text": "Second insight"},
            ],
            "right": [],
        },
    }
    result = split_slide(slide)

    assert len(result) == 1
    assert result[0] is slide


def test_split_three_column():
    """Three-column slide with 6 blocks per column should split into 2 slides."""
    # 6 cards * 126px each + 5*10 gaps = 756 + 50 = 806px > 575px
    slide = make_three_column_slide(per_col=6, bullets=3)
    result = split_slide(slide)

    assert len(result) == 2
    for s in result:
        assert s["layout"] == "three-column"


def test_continuation_subtitle():
    """After split, the second slide should have '(cont.)' appended to its subtitle."""
    slide = make_two_column_slide(left_count=8, right_count=0, bullets=3)
    result = split_slide(slide)

    assert len(result) == 2
    subtitle = result[1]["data"].get("subtitle", "")
    assert "(cont.)" in subtitle


def test_continuation_subtitle_no_existing_subtitle():
    """Continuation slide with no prior subtitle should have subtitle set to '(cont.)'."""
    slide = {
        "layout": "two-column",
        "data": {
            "title": "No Subtitle Slide",
            # No 'subtitle' key
            "left": [make_card(i, bullets=3) for i in range(8)],
            "right": [],
        },
    }
    result = split_slide(slide)

    assert len(result) == 2
    assert result[1]["data"]["subtitle"] == "(cont.)"


def test_non_columnar_layout_unchanged():
    """A 'title' layout slide is returned unchanged without inspection."""
    slide = {
        "layout": "title",
        "data": {
            "title": "Welcome",
            "subtitle": "An intro slide",
            "icons": [{"icon": "rocket", "label": "Fast"}],
        },
    }
    result = split_slide(slide)

    assert len(result) == 1
    assert result[0] is slide


def test_split_preserves_title():
    """Both split slides should retain the original title."""
    original_title = "My Important Title"
    slide = {
        "layout": "two-column",
        "data": {
            "title": original_title,
            "left": [make_card(i, bullets=3) for i in range(8)],
            "right": [],
        },
    }
    result = split_slide(slide)

    assert len(result) == 2
    for s in result:
        assert s["data"]["title"] == original_title


def test_split_does_not_mutate_original():
    """split_slide() must not mutate the original slide dict."""
    slide = make_two_column_slide(left_count=8, right_count=0, bullets=3)
    original_left_count = len(slide["data"]["left"])
    original_subtitle = slide["data"].get("subtitle", "")
    original_deep = copy.deepcopy(slide)

    _ = split_slide(slide)

    # Original should be completely unchanged
    assert slide == original_deep
    assert len(slide["data"]["left"]) == original_left_count
    assert slide["data"].get("subtitle", "") == original_subtitle


def test_data_table_split():
    """Data-table slide with 4 large sections should split into 2 slides."""
    # Each section has 20 rows: 35 + 30 + 20*33 = 725px > 575px USABLE_HEIGHT
    # Having 4 such sections: analyze_slide triggers on section 1 (single-section column overflow)
    slide = make_data_table_slide(section_count=4, rows_per_section=20)
    result = split_slide(slide)

    assert len(result) == 2
    for s in result:
        assert s["layout"] == "data-table"
        assert len(s["data"]["sections"]) > 0


def test_fit_split_empty_list():
    """_fit_split([]) returns ([], [])."""
    fits, remainder = _fit_split([])
    assert fits == []
    assert remainder == []
