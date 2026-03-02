"""
LayoutAnalyzer — estimates rendered height of slide content
and warns about overflow at build time.
"""

import math

USABLE_HEIGHT = 575
COLUMN_GAP = 10
HEADER_HEIGHT = 65

SIZE_MODEL = {
    "card": {"base": 60, "per_item": 22, "item_key": "bullets"},
    "solution-box": {"base": 80, "per_item": 28, "item_key": "items"},
    "stat-grid": {"base": 0, "per_row": 55, "row_gap": 15, "cols_key": "cols", "items_key": "stats"},
    "table": {"base": 35, "per_item": 33, "item_key": "rows", "section_title": 30},
    "dist-bars": {"base": 10, "per_item": 28, "item_key": "bars"},
    "val-bars": {"base": 0, "per_item": 30, "item_key": "items"},
    "unit-grid": {"base": 10, "per_item": 65, "item_key": "tiers"},
    "insight": {"base": 45, "per_item": 0},
    "value-prop": {"base": 45, "per_item": 0},
    "takeaway": {"base": 40, "per_item": 0},
}

DEFAULT_BLOCK_HEIGHT = 40

COLUMNAR_LAYOUTS = {"two-column", "three-column", "data-table", "stat-grid"}


class LayoutAnalyzer:
    """Estimates slide content height and detects overflow."""

    @staticmethod
    def estimate_block_height(block: dict) -> int:
        block_type = block.get("type", "")
        model = SIZE_MODEL.get(block_type)

        if model is None:
            return DEFAULT_BLOCK_HEIGHT

        if block_type == "stat-grid":
            items = block.get(model["items_key"], [])
            cols = block.get(model.get("cols_key", "cols"), 2)
            rows = math.ceil(len(items) / cols) if cols > 0 else 0
            if rows == 0:
                return 0
            return rows * model["per_row"] + (rows - 1) * model["row_gap"]

        base = model["base"]
        if block_type == "table" and block.get("section_title"):
            base += model.get("section_title", 0)

        item_key = model.get("item_key")
        if item_key:
            items = block.get(item_key, [])
            return base + len(items) * model["per_item"]

        return base

    @staticmethod
    def estimate_column_height(blocks: list[dict]) -> int:
        if not blocks:
            return 0
        total = sum(LayoutAnalyzer.estimate_block_height(b) for b in blocks)
        gaps = (len(blocks) - 1) * COLUMN_GAP
        return total + gaps

    @staticmethod
    def _get_columns(slide: dict) -> dict[str, list[dict]]:
        layout = slide.get("layout", "")
        data = slide.get("data", {})

        if layout == "two-column":
            return {
                "left": data.get("left", []),
                "right": data.get("right", []),
            }
        elif layout == "three-column":
            columns = data.get("columns", [[], [], []])
            return {f"col {i+1}": col for i, col in enumerate(columns)}
        elif layout == "data-table":
            sections = data.get("sections", [])
            return {f"section {i+1}": [s] if isinstance(s, dict) else []
                    for i, s in enumerate(sections)}
        return {}

    @staticmethod
    def analyze_slide(slide: dict, index: int) -> dict | None:
        layout = slide.get("layout", "")
        if layout not in COLUMNAR_LAYOUTS:
            return None

        columns = LayoutAnalyzer._get_columns(slide)
        for col_name, blocks in columns.items():
            height = LayoutAnalyzer.estimate_column_height(blocks)
            if height > USABLE_HEIGHT:
                overflow_pct = round((height - USABLE_HEIGHT) / USABLE_HEIGHT * 100)
                return {
                    "slide_index": index,
                    "layout": layout,
                    "column": col_name,
                    "estimated_px": height,
                    "usable_px": USABLE_HEIGHT,
                    "overflow_pct": overflow_pct,
                }
        return None

    @staticmethod
    def compute_density(slide: dict) -> str:
        layout = slide.get("layout", "")
        if layout not in COLUMNAR_LAYOUTS:
            return "normal"

        columns = LayoutAnalyzer._get_columns(slide)
        max_height = max(
            (LayoutAnalyzer.estimate_column_height(blocks) for blocks in columns.values()),
            default=0,
        )
        if max_height > USABLE_HEIGHT * 0.85:
            return "high"
        return "normal"
