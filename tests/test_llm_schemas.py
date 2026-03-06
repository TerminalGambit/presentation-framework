"""Tests for pf.llm_schemas — per-layout Pydantic models with cardinality constraints.

Verifies that:
- All 11 layout models exist and are importable
- model_json_schema() produces maxItems on list fields
- model_json_schema() produces maxLength on string fields
- get_layout_schema() returns correct classes
- PresentationOutput wrapper model has the expected fields
"""

import json

import pytest

from pf.llm_schemas import (
    CardBlock,
    ChartSlide,
    ClosingSlide,
    DataTableSlide,
    ImageSlide,
    PresentationOutput,
    QuoteSlide,
    SectionSlide,
    StatGridSlide,
    ThreeColumnSlide,
    TimelineSlide,
    TitleSlide,
    TwoColumnSlide,
    get_all_schemas,
    get_layout_schema,
)
from pf.mcp_server import LAYOUT_DESCRIPTIONS


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


def _collect_all_constraints(schema: dict, key: str) -> list:
    """Recursively walk JSON Schema and collect all occurrences of ``key``."""
    results = []
    if isinstance(schema, dict):
        if key in schema:
            results.append(schema[key])
        for v in schema.values():
            results.extend(_collect_all_constraints(v, key))
    elif isinstance(schema, list):
        for item in schema:
            results.extend(_collect_all_constraints(item, key))
    return results


# ---------------------------------------------------------------------------
# Test 1: Every schema has at least one maxItems or maxLength constraint
# ---------------------------------------------------------------------------


class TestAllSchemasHaveConstraints:
    """Each of the 11 layout schemas must encode at least one size constraint."""

    @pytest.mark.parametrize("layout_name,model_class", list(get_all_schemas().items()))
    def test_schema_has_maxitems_or_maxlength(self, layout_name, model_class):
        schema = model_class.model_json_schema()
        max_items = _collect_all_constraints(schema, "maxItems")
        max_length = _collect_all_constraints(schema, "maxLength")
        assert max_items or max_length, (
            f"Layout '{layout_name}' has no maxItems or maxLength constraints "
            f"in its JSON Schema."
        )


# ---------------------------------------------------------------------------
# Test 2: TimelineSlide — minItems and maxItems on steps
# ---------------------------------------------------------------------------


class TestTimelineSchemaConstraints:
    def test_timeline_has_max_items(self):
        schema = TimelineSlide.model_json_schema()
        steps = schema["properties"]["steps"]
        assert steps.get("maxItems") == 6, (
            f"Expected maxItems=6 on steps, got {steps}"
        )

    def test_timeline_has_min_items(self):
        schema = TimelineSlide.model_json_schema()
        steps = schema["properties"]["steps"]
        assert steps.get("minItems") == 2, (
            f"Expected minItems=2 on steps, got {steps}"
        )


# ---------------------------------------------------------------------------
# Test 3: TwoColumnSlide — maxItems on left and right
# ---------------------------------------------------------------------------


class TestTwoColumnSchemaConstraints:
    def test_left_has_max_items(self):
        schema = TwoColumnSlide.model_json_schema()
        left = schema["properties"]["left"]
        assert left.get("maxItems") == 3, (
            f"Expected maxItems=3 on left, got {left}"
        )

    def test_right_has_max_items(self):
        schema = TwoColumnSlide.model_json_schema()
        right = schema["properties"]["right"]
        assert right.get("maxItems") == 3, (
            f"Expected maxItems=3 on right, got {right}"
        )


# ---------------------------------------------------------------------------
# Test 4: CardBlock — maxItems on bullets
# ---------------------------------------------------------------------------


class TestCardBlockConstraints:
    def test_bullets_has_max_items(self):
        schema = CardBlock.model_json_schema()
        bullets = schema["properties"]["bullets"]
        # bullets may be anyOf (optional), so check the array variant
        if "anyOf" in bullets:
            array_variants = [v for v in bullets["anyOf"] if v.get("type") == "array"]
            assert array_variants, "bullets has no array variant in anyOf"
            arr = array_variants[0]
        else:
            arr = bullets
        assert arr.get("maxItems") == 4, (
            f"Expected maxItems=4 on bullets, got {arr}"
        )


# ---------------------------------------------------------------------------
# Test 5: TitleSlide — maxLength on title
# ---------------------------------------------------------------------------


class TestTitleSlideConstraints:
    def test_title_has_max_length(self):
        schema = TitleSlide.model_json_schema()
        title_field = schema["properties"]["title"]
        assert title_field.get("maxLength") == 80, (
            f"Expected maxLength=80 on title, got {title_field}"
        )


# ---------------------------------------------------------------------------
# Test 6 & 7: get_layout_schema — known and unknown layouts
# ---------------------------------------------------------------------------


class TestGetLayoutSchema:
    def test_returns_correct_class_for_timeline(self):
        result = get_layout_schema("timeline")
        assert result is TimelineSlide

    def test_returns_correct_class_for_two_column(self):
        result = get_layout_schema("two-column")
        assert result is TwoColumnSlide

    def test_returns_correct_class_for_each_layout(self):
        expected = {
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
        for name, cls in expected.items():
            assert get_layout_schema(name) is cls, (
                f"get_layout_schema('{name}') returned wrong class"
            )

    def test_unknown_layout_returns_none(self):
        assert get_layout_schema("nonexistent") is None

    def test_empty_string_returns_none(self):
        assert get_layout_schema("") is None


# ---------------------------------------------------------------------------
# Test 8: All LAYOUT_DESCRIPTIONS keys are covered by get_all_schemas
# ---------------------------------------------------------------------------


class TestAllLayoutsCovered:
    def test_layout_names_match_mcp_descriptions(self):
        schema_keys = set(get_all_schemas().keys())
        layout_desc_keys = set(LAYOUT_DESCRIPTIONS.keys())
        missing = layout_desc_keys - schema_keys
        extra = schema_keys - layout_desc_keys
        assert not missing, f"Layouts in LAYOUT_DESCRIPTIONS missing from schemas: {missing}"
        assert not extra, f"Schemas with no matching LAYOUT_DESCRIPTIONS entry: {extra}"

    def test_exactly_11_schemas(self):
        schemas = get_all_schemas()
        assert len(schemas) == 11, f"Expected 11 schemas, got {len(schemas)}: {list(schemas.keys())}"


# ---------------------------------------------------------------------------
# Test 9: PresentationOutput model structure
# ---------------------------------------------------------------------------


class TestPresentationOutputModel:
    def test_has_yaml_config_field(self):
        schema = PresentationOutput.model_json_schema()
        assert "yaml_config" in schema["properties"], (
            "PresentationOutput must have a 'yaml_config' field"
        )

    def test_yaml_config_is_string_type(self):
        schema = PresentationOutput.model_json_schema()
        yaml_field = schema["properties"]["yaml_config"]
        assert yaml_field.get("type") == "string", (
            f"yaml_config should be string type, got: {yaml_field}"
        )

    def test_has_metrics_field(self):
        schema = PresentationOutput.model_json_schema()
        assert "metrics" in schema["properties"], (
            "PresentationOutput must have a 'metrics' field"
        )

    def test_instantiation_with_yaml_string(self):
        output = PresentationOutput(
            yaml_config="theme:\n  primary: '#1a1a2e'",
            metrics={"revenue": 1000000},
        )
        assert output.yaml_config.startswith("theme:")
        assert output.metrics["revenue"] == 1000000

    def test_metrics_defaults_to_empty_dict(self):
        output = PresentationOutput(yaml_config="theme: {}")
        assert output.metrics == {}


# ---------------------------------------------------------------------------
# Test 10: Every schema is a valid JSON Schema object
# ---------------------------------------------------------------------------


class TestSchemaJsonIsValid:
    @pytest.mark.parametrize("layout_name,model_class", list(get_all_schemas().items()))
    def test_schema_is_valid_json_schema(self, layout_name, model_class):
        schema = model_class.model_json_schema()
        assert isinstance(schema, dict), f"Schema for '{layout_name}' is not a dict"
        assert schema.get("type") == "object", (
            f"Schema for '{layout_name}' must have type='object', got: {schema.get('type')}"
        )
        assert "properties" in schema, (
            f"Schema for '{layout_name}' must have a 'properties' key"
        )

    @pytest.mark.parametrize("layout_name,model_class", list(get_all_schemas().items()))
    def test_schema_is_json_serialisable(self, layout_name, model_class):
        schema = model_class.model_json_schema()
        serialised = json.dumps(schema)
        roundtripped = json.loads(serialised)
        assert roundtripped == schema, (
            f"Schema for '{layout_name}' failed JSON roundtrip"
        )


# ---------------------------------------------------------------------------
# Additional constraint spot-checks
# ---------------------------------------------------------------------------


class TestAdditionalConstraints:
    def test_quote_slide_text_max_length(self):
        schema = QuoteSlide.model_json_schema()
        text_field = schema["properties"]["text"]
        assert text_field.get("maxLength") == 300

    def test_section_slide_title_max_length(self):
        schema = SectionSlide.model_json_schema()
        title_field = schema["properties"]["title"]
        assert title_field.get("maxLength") == 60

    def test_chart_slide_labels_max_items(self):
        schema = ChartSlide.model_json_schema()
        labels_field = schema["properties"]["labels"]
        assert labels_field.get("maxItems") == 12

    def test_closing_slide_info_items_max_items(self):
        schema = ClosingSlide.model_json_schema()
        info_items = schema["properties"]["info_items"]
        # Field is Optional so may be wrapped in anyOf
        if "anyOf" in info_items:
            array_variants = [v for v in info_items["anyOf"] if v.get("type") == "array"]
            assert array_variants, "info_items has no array variant"
            arr = array_variants[0]
        else:
            arr = info_items
        assert arr.get("maxItems") == 4

    def test_three_column_columns_max_items(self):
        schema = ThreeColumnSlide.model_json_schema()
        columns_field = schema["properties"]["columns"]
        assert columns_field.get("maxItems") == 3

    def test_data_table_sections_max_items(self):
        schema = DataTableSlide.model_json_schema()
        sections_field = schema["properties"]["sections"]
        assert sections_field.get("maxItems") == 2

    def test_stat_grid_columns_max_items(self):
        schema = StatGridSlide.model_json_schema()
        columns_field = schema["properties"]["columns"]
        assert columns_field.get("maxItems") == 2

    def test_title_slide_features_max_items(self):
        schema = TitleSlide.model_json_schema()
        features_field = schema["properties"]["features"]
        # Optional field may use anyOf
        if "anyOf" in features_field:
            array_variants = [v for v in features_field["anyOf"] if v.get("type") == "array"]
            assert array_variants, "features has no array variant"
            arr = array_variants[0]
        else:
            arr = features_field
        assert arr.get("maxItems") == 4

    def test_image_slide_layout_field(self):
        schema = ImageSlide.model_json_schema()
        assert "image" in schema["properties"]
        assert "position" in schema["properties"]

    def test_get_all_schemas_returns_copy(self):
        """Modifying the returned dict should not affect the registry."""
        schemas1 = get_all_schemas()
        schemas1["injected"] = None
        schemas2 = get_all_schemas()
        assert "injected" not in schemas2
