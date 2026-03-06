"""
Per-layout Pydantic v2 models for LLM structured output.

Each model encodes cardinality constraints (maxItems on list fields,
maxLength on string fields) derived from LayoutAnalyzer.SIZE_MODEL and
USABLE_HEIGHT (575px). These models serve as ``response_model`` for the
``instructor`` library so LLMs cannot generate slides that would overflow.

Usage::

    from pf.llm_schemas import get_layout_schema, TwoColumnSlide
    schema = TwoColumnSlide.model_json_schema()
    model_class = get_layout_schema("two-column")
"""

from __future__ import annotations

from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Reusable block models
# ---------------------------------------------------------------------------


class CardBlock(BaseModel):
    """Card block — title, optional text/icon, short bullet list.

    Constraint derivation (SIZE_MODEL["card"]):
      base=60px, per_item=22px, item_key="bullets"
      4 bullets → 60 + 4×22 = 148 px (fits in a 575px column)
    """

    type: Literal["card"] = "card"
    title: str = Field(max_length=60)
    text: Optional[str] = Field(default=None, max_length=200)
    bullets: Optional[list[Annotated[str, Field(max_length=120)]]] = Field(
        default=None, max_length=4
    )
    icon: Optional[str] = Field(default=None, max_length=40)


class SolutionBoxBlock(BaseModel):
    """Solution-box block — badge, title, checklist items.

    Constraint derivation (SIZE_MODEL["solution-box"]):
      base=80px, per_item=28px, item_key="items"
      4 items → 80 + 4×28 = 192 px
    """

    type: Literal["solution-box"] = "solution-box"
    badge: Optional[str] = Field(default=None, max_length=40)
    title: str = Field(max_length=60)
    items: list[Annotated[str, Field(max_length=120)]] = Field(max_length=4)
    icon: Optional[str] = Field(default=None, max_length=40)


class StatItem(BaseModel):
    """Single key-value statistic displayed in a stat-grid."""

    value: str = Field(max_length=20)
    label: str = Field(max_length=40)


class StatGridBlock(BaseModel):
    """Stat-grid block — grid of key/value statistics.

    Constraint derivation (SIZE_MODEL["stat-grid"]):
      per_row=55px, row_gap=15px, default cols=2
      6 stats, 2 cols → 3 rows × 55 + 2×15 = 195 px
    """

    type: Literal["stat-grid"] = "stat-grid"
    cols: int = Field(default=2, ge=1, le=4)
    stats: list[StatItem] = Field(max_length=6)


class TableBlock(BaseModel):
    """Table block — headers, rows, optional highlighting and footnote.

    Constraint derivation (SIZE_MODEL["table"]):
      base=35px, per_item=33px, item_key="rows"
      8 rows → 35 + 8×33 = 299 px (fits in a 575px column)
    """

    type: Literal["table"] = "table"
    headers: list[Annotated[str, Field(max_length=60)]] = Field(max_length=8)
    rows: list[list[Annotated[str, Field(max_length=80)]]] = Field(max_length=8)
    winner_rows: Optional[list[int]] = Field(default=None)
    footnote: Optional[str] = Field(default=None, max_length=200)


class DistBarItem(BaseModel):
    """Single distribution-bar entry."""

    label: str = Field(max_length=60)
    value: float
    color: Optional[str] = Field(default=None, max_length=20)


class DistBarBlock(BaseModel):
    """Distribution-bars block — horizontal percentage bars.

    Constraint derivation (SIZE_MODEL["dist-bars"]):
      base=10px, per_item=28px, item_key="bars"
      8 bars → 10 + 8×28 = 234 px
    """

    type: Literal["dist-bars"] = "dist-bars"
    bars: list[DistBarItem] = Field(max_length=8)


class ValBarItem(BaseModel):
    """Single value-bar entry."""

    label: str = Field(max_length=60)
    value: float
    max_value: Optional[float] = Field(default=None)


class ValBarBlock(BaseModel):
    """Value-bars block — vertical value bars.

    Constraint derivation (SIZE_MODEL["val-bars"]):
      base=0px, per_item=30px, item_key="items"
      6 items → 6×30 = 180 px
    """

    type: Literal["val-bars"] = "val-bars"
    items: list[ValBarItem] = Field(max_length=6)


class InsightBlock(BaseModel):
    """Insight/callout block — highlighted key finding text."""

    type: Literal["insight"] = "insight"
    text: str = Field(max_length=300)
    icon: Optional[str] = Field(default=None, max_length=40)


# Discriminated union of all block types for column fields
ContentBlock = Annotated[
    Union[
        CardBlock,
        SolutionBoxBlock,
        StatGridBlock,
        TableBlock,
        DistBarBlock,
        ValBarBlock,
        InsightBlock,
    ],
    Field(discriminator="type"),
]


# ---------------------------------------------------------------------------
# Per-layout slide models
# ---------------------------------------------------------------------------


class TitleSlide(BaseModel):
    """Title / opening slide.

    Maps to layout: title
    """

    layout: Literal["title"] = "title"
    title: str = Field(max_length=80)
    subtitle: Optional[str] = Field(default=None, max_length=120)
    tagline: Optional[str] = Field(default=None, max_length=200)
    footer: Optional[str] = Field(default=None, max_length=100)
    features: Optional[
        list[
            Annotated[
                dict,
                Field(description="Feature item with 'icon' and 'label' keys"),
            ]
        ]
    ] = Field(default=None, max_length=4)


class TwoColumnSlide(BaseModel):
    """Two-column slide — primary workhorse layout.

    Each column accepts up to 3 content blocks so both columns fit within
    USABLE_HEIGHT (575px). Maps to layout: two-column.
    """

    layout: Literal["two-column"] = "two-column"
    title: str = Field(max_length=80)
    subtitle: Optional[str] = Field(default=None, max_length=120)
    left: list[ContentBlock] = Field(max_length=3)
    right: list[ContentBlock] = Field(max_length=3)


class ThreeColumnSlide(BaseModel):
    """Three-column comparison slide.

    columns is a list of exactly 3 column lists, each holding up to 2 blocks
    (narrower columns have less vertical space). Maps to layout: three-column.
    """

    layout: Literal["three-column"] = "three-column"
    title: str = Field(max_length=80)
    subtitle: Optional[str] = Field(default=None, max_length=120)
    columns: list[list[ContentBlock]] = Field(max_length=3)


class DataTableSection(BaseModel):
    """One section inside a data-table slide."""

    section_title: Optional[str] = Field(default=None, max_length=80)
    section_icon: Optional[str] = Field(default=None, max_length=40)
    table: Optional[TableBlock] = None
    insight: Optional[InsightBlock] = None


class DataTableSlide(BaseModel):
    """Data-table slide — benchmark tables with optional insights.

    Up to 2 sections fit side by side. Maps to layout: data-table.
    """

    layout: Literal["data-table"] = "data-table"
    title: str = Field(max_length=80)
    subtitle: Optional[str] = Field(default=None, max_length=120)
    sections: list[DataTableSection] = Field(max_length=2)


class StatGridSlide(BaseModel):
    """Stat-grid slide — KPI dashboard with two content columns.

    columns is a list of up to 2 column lists. Maps to layout: stat-grid.
    """

    layout: Literal["stat-grid"] = "stat-grid"
    title: str = Field(max_length=80)
    subtitle: Optional[str] = Field(default=None, max_length=120)
    columns: list[list[ContentBlock]] = Field(max_length=2)


class ChartSlide(BaseModel):
    """Interactive Plotly chart slide.

    Requires theme.charts: true. Maps to layout: chart.
    """

    layout: Literal["chart"] = "chart"
    title: Optional[str] = Field(default=None, max_length=80)
    subtitle: Optional[str] = Field(default=None, max_length=120)
    chart_type: Literal["bar", "line", "pie", "scatter"] = "bar"
    labels: list[Annotated[str, Field(max_length=60)]] = Field(max_length=12)
    values: list[float] = Field(max_length=12)


class ClosingInfoItem(BaseModel):
    """Contact pill or info item for the closing slide."""

    type: Literal["pill", "info"] = "info"
    icon: str = Field(
        max_length=60,
        description="Full FontAwesome class, e.g. 'fa-brands fa-github'",
    )
    text: str = Field(max_length=120)


class ClosingSlide(BaseModel):
    """Thank-you / Q&A closing slide. Maps to layout: closing."""

    layout: Literal["closing"] = "closing"
    title: str = Field(max_length=60)
    subtitle: Optional[str] = Field(default=None, max_length=120)
    info_items: Optional[list[ClosingInfoItem]] = Field(default=None, max_length=4)
    footer: Optional[str] = Field(default=None, max_length=100)


class ImageSlide(BaseModel):
    """Full-bleed or split image slide. Maps to layout: image."""

    layout: Literal["image"] = "image"
    image: str = Field(max_length=500, description="URL or file path to image")
    position: Literal["full", "split"] = "full"
    title: Optional[str] = Field(default=None, max_length=80)
    caption: Optional[str] = Field(default=None, max_length=200)


class SectionSlide(BaseModel):
    """Section divider slide. Maps to layout: section."""

    layout: Literal["section"] = "section"
    title: str = Field(max_length=60)
    subtitle: Optional[str] = Field(default=None, max_length=120)
    number: Optional[int] = Field(default=None, ge=1)


class QuoteSlide(BaseModel):
    """Centered blockquote slide. Maps to layout: quote."""

    layout: Literal["quote"] = "quote"
    text: str = Field(max_length=300)
    author: Optional[str] = Field(default=None, max_length=60)
    role: Optional[str] = Field(default=None, max_length=80)


class TimelineStep(BaseModel):
    """One step in a timeline slide."""

    icon: Optional[str] = Field(default=None, max_length=40)
    title: str = Field(max_length=60)
    description: Optional[str] = Field(default=None, max_length=200)


class TimelineSlide(BaseModel):
    """Horizontal timeline / roadmap slide.

    Requires 2-6 steps for the layout to render correctly.
    Maps to layout: timeline.
    """

    layout: Literal["timeline"] = "timeline"
    title: str = Field(max_length=80)
    steps: list[TimelineStep] = Field(min_length=2, max_length=6)


# ---------------------------------------------------------------------------
# Presentation-level wrapper model
# ---------------------------------------------------------------------------


class PresentationOutput(BaseModel):
    """Complete presentation output produced by the LLM generation pipeline.

    ``yaml_config`` is the full content of ``presentation.yaml`` as a string.
    ``metrics`` is the parsed content of ``metrics.json`` as a dictionary.
    """

    yaml_config: str = Field(
        description="Full presentation.yaml content as a YAML string"
    )
    metrics: dict = Field(
        default_factory=dict,
        description="metrics.json data as a Python dictionary",
    )


# ---------------------------------------------------------------------------
# Registry / lookup
# ---------------------------------------------------------------------------

_LAYOUT_REGISTRY: dict[str, type[BaseModel]] = {
    "title": TitleSlide,
    "two-column": TwoColumnSlide,
    "three-column": ThreeColumnSlide,
    "data-table": DataTableSlide,
    "stat-grid": StatGridSlide,
    "chart": ChartSlide,
    "closing": ClosingSlide,
    "image": ImageSlide,
    "section": SectionSlide,
    "quote": QuoteSlide,
    "timeline": TimelineSlide,
}


def get_layout_schema(layout_name: str) -> type[BaseModel] | None:
    """Return the Pydantic model class for a given layout name.

    Returns ``None`` for unknown layout names.

    Example::

        model_class = get_layout_schema("timeline")
        schema = model_class.model_json_schema()
    """
    return _LAYOUT_REGISTRY.get(layout_name)


def get_all_schemas() -> dict[str, type[BaseModel]]:
    """Return a mapping of all layout names to their Pydantic model classes.

    Example::

        for name, model in get_all_schemas().items():
            print(name, model.model_json_schema())
    """
    return dict(_LAYOUT_REGISTRY)
