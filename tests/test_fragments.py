"""Tests for slide fragments / progressive reveal (MEDIA-02)."""
import pytest
from pf.builder import PresentationBuilder

THEME_BASE = {
    "primary": "#1C2537",
    "accent": "#C4A962",
    "fonts": {"heading": "Playfair Display", "subheading": "Montserrat", "body": "Lato"},
}


def _render(slides):
    """Helper: render slides and return list of HTML strings."""
    b = PresentationBuilder()
    b.config = {
        "meta": {"title": "Test"},
        "theme": THEME_BASE,
        "slides": slides,
    }
    b.metrics = {}
    features = b._scan_features(slides)
    return [b.render_slide(s, i, features=features) for i, s in enumerate(slides)]


class TestBlockFragment:
    """Fragment on a block (whole block reveals at once)."""

    def test_card_with_fragment_has_class(self):
        slides = [{"layout": "two-column", "data": {
            "title": "T",
            "left": [{"type": "card", "title": "Step 1", "text": "First", "fragment": True}],
            "right": [],
        }}]
        htmls = _render(slides)
        assert "pf-fragment" in htmls[0]

    def test_card_without_fragment_no_class(self):
        slides = [{"layout": "two-column", "data": {
            "title": "T",
            "left": [{"type": "card", "title": "Step 1", "text": "First"}],
            "right": [],
        }}]
        htmls = _render(slides)
        assert "pf-fragment" not in htmls[0]

    def test_code_block_with_fragment(self):
        slides = [{"layout": "two-column", "data": {
            "title": "T",
            "left": [{"type": "code", "code": "x=1", "fragment": True}],
            "right": [],
        }}]
        htmls = _render(slides)
        assert "pf-fragment" in htmls[0]


class TestBulletFragment:
    """Fragment on individual bullets within a block."""

    def test_bullet_with_fragment_has_class(self):
        """Bullets marked fragment: true should have pf-fragment class on the div."""
        slides = [{"layout": "two-column", "data": {
            "title": "T",
            "left": [{"type": "card", "title": "Steps", "bullets": [
                {"text": "Point A", "fragment": True},
                {"text": "Point B", "fragment": True},
                {"text": "Point C"},
            ]}],
            "right": [],
        }}]
        htmls = _render(slides)
        # At least some elements should have pf-fragment
        html = htmls[0]
        # Count pf-fragment occurrences — should be 2 (for Point A and B)
        assert html.count("pf-fragment") >= 2

    def test_plain_string_bullets_still_work(self):
        """Plain string bullets (backward compat) should render without fragment class."""
        slides = [{"layout": "two-column", "data": {
            "title": "T",
            "left": [{"type": "card", "title": "Steps", "bullets": [
                "Point A",
                "Point B",
            ]}],
            "right": [],
        }}]
        htmls = _render(slides)
        assert "Point A" in htmls[0]
        assert "Point B" in htmls[0]
        assert "pf-fragment" not in htmls[0]


class TestFragmentCSS:
    """Verify fragment CSS is in the theme."""

    def test_components_css_has_fragment_styles(self):
        from pathlib import Path
        css_path = Path(__file__).parent.parent / "theme" / "components.css"
        css = css_path.read_text()
        assert ".pf-fragment" in css
        assert "opacity: 0" in css or "opacity:0" in css
        assert ".pf-fragment.visible" in css


class TestFragmentNavigator:
    """Verify present.html.j2 has fragment integration."""

    def test_navigator_has_fragment_logic(self):
        from pathlib import Path
        tmpl_path = Path(__file__).parent.parent / "templates" / "present.html.j2"
        tmpl = tmpl_path.read_text()
        assert "pf-fragment" in tmpl, "Navigator must reference fragment class"


class TestCardFragmentPartial:
    """Verify card.html.j2 partial has fragment support."""

    def test_card_partial_accepts_fragment_parameter(self):
        from pathlib import Path
        card_path = Path(__file__).parent.parent / "templates" / "partials" / "card.html.j2"
        card = card_path.read_text()
        assert "fragment" in card, "challenge_card must accept fragment parameter"
        assert "pf-fragment" in card, "challenge_card must apply pf-fragment class"

    def test_card_partial_supports_dict_bullets(self):
        from pathlib import Path
        card_path = Path(__file__).parent.parent / "templates" / "partials" / "card.html.j2"
        card = card_path.read_text()
        assert "mapping" in card or "bullet.text" in card, "Bullet loop must handle dict bullets"
