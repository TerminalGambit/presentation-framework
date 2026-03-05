"""Tests for pf.analyzer.LayoutAnalyzer."""

import pytest
from pf.analyzer import LayoutAnalyzer


class TestBlockHeight:
    def test_card_base_height(self):
        block = {"type": "card", "icon": "bolt", "title": "Test", "text": "Desc"}
        height = LayoutAnalyzer.estimate_block_height(block)
        assert height == 60

    def test_card_with_bullets(self):
        block = {"type": "card", "icon": "bolt", "title": "Test", "text": "Desc",
                 "bullets": ["a", "b", "c"]}
        height = LayoutAnalyzer.estimate_block_height(block)
        assert height == 126

    def test_stat_grid_2_cols(self):
        block = {"type": "stat-grid", "stats": [
            {"value": "128", "label": "Assets"},
            {"value": "9", "label": "Categories"},
            {"value": "17", "label": "Feeds"},
            {"value": "36", "label": "Accounts"},
        ], "cols": 2}
        height = LayoutAnalyzer.estimate_block_height(block)
        assert height == 125

    def test_table_height(self):
        block = {"type": "table", "headers": ["Name", "Score"],
                 "rows": [["A", "90"], ["B", "85"], ["C", "80"]]}
        height = LayoutAnalyzer.estimate_block_height(block)
        assert height == 134

    def test_insight_height(self):
        block = {"type": "insight", "text": "Key finding here"}
        height = LayoutAnalyzer.estimate_block_height(block)
        assert height == 45

    def test_solution_box_height(self):
        block = {"type": "solution-box", "title": "Solution",
                 "items": ["item1", "item2", "item3"]}
        height = LayoutAnalyzer.estimate_block_height(block)
        assert height == 164

    def test_unknown_block_default(self):
        block = {"type": "html", "content": "<p>hello</p>"}
        height = LayoutAnalyzer.estimate_block_height(block)
        assert height == 40


class TestColumnHeight:
    def test_single_block(self):
        col = [{"type": "insight", "text": "Note"}]
        height = LayoutAnalyzer.estimate_column_height(col)
        assert height == 45

    def test_multiple_blocks_with_gaps(self):
        col = [
            {"type": "insight", "text": "A"},
            {"type": "insight", "text": "B"},
        ]
        height = LayoutAnalyzer.estimate_column_height(col)
        assert height == 100

    def test_empty_column(self):
        assert LayoutAnalyzer.estimate_column_height([]) == 0


class TestSlideAnalysis:
    def test_two_column_within_limits(self):
        slide = {
            "layout": "two-column",
            "data": {
                "title": "Test",
                "left": [{"type": "insight", "text": "Short"}],
                "right": [{"type": "insight", "text": "Short"}],
            },
        }
        result = LayoutAnalyzer.analyze_slide(slide, 0)
        assert result is None

    def test_two_column_overflow_warning(self):
        cards = [{"type": "card", "icon": "bolt", "title": f"Card {i}", "text": "Desc"}
                 for i in range(12)]
        slide = {
            "layout": "two-column",
            "data": {
                "title": "Overflowing",
                "left": cards,
                "right": [{"type": "insight", "text": "Short"}],
            },
        }
        result = LayoutAnalyzer.analyze_slide(slide, 2)
        assert result is not None
        assert "left" in result["column"]
        assert result["estimated_px"] > 575
        assert result["slide_index"] == 2

    def test_title_layout_no_analysis(self):
        slide = {"layout": "title", "data": {"title": "Hello"}}
        result = LayoutAnalyzer.analyze_slide(slide, 0)
        assert result is None

    def test_three_column_overflow(self):
        cards = [{"type": "card", "icon": "bolt", "title": f"Card {i}", "text": "Desc"}
                 for i in range(10)]
        slide = {
            "layout": "three-column",
            "data": {
                "title": "Dense",
                "columns": [cards, [], []],
            },
        }
        result = LayoutAnalyzer.analyze_slide(slide, 0)
        assert result is not None


class TestDensity:
    def test_normal_density(self):
        slide = {
            "layout": "two-column",
            "data": {
                "title": "Light",
                "left": [{"type": "insight", "text": "Short"}],
                "right": [{"type": "insight", "text": "Short"}],
            },
        }
        density = LayoutAnalyzer.compute_density(slide)
        assert density == "normal"

    def test_high_density(self):
        cards = [{"type": "card", "icon": "bolt", "title": f"C{i}", "text": "D"}
                 for i in range(8)]
        slide = {
            "layout": "two-column",
            "data": {
                "title": "Dense",
                "left": cards,
                "right": cards,
            },
        }
        density = LayoutAnalyzer.compute_density(slide)
        assert density == "high"
