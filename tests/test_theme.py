"""Tests for expanded theme options."""
from pf.builder import PresentationBuilder


class TestExpandedTheme:
    def test_secondary_accent_generated(self):
        b = PresentationBuilder()
        theme = {
            "primary": "#1C2537",
            "accent": "#C4A962",
            "secondary_accent": "#5B8FA8",
        }
        css = b.generate_variables_css(theme)
        assert "--pf-secondary-accent" in css
        assert "#5B8FA8" in css

    def test_no_secondary_accent_default(self):
        b = PresentationBuilder()
        theme = {"primary": "#1C2537", "accent": "#C4A962"}
        css = b.generate_variables_css(theme)
        assert "--pf-secondary-accent" in css

    def test_style_preset_modern(self):
        b = PresentationBuilder()
        theme = {"primary": "#1C2537", "accent": "#C4A962", "style": "modern"}
        css = b.generate_variables_css(theme)
        assert "--pf-radius-lg" in css

    def test_style_preset_minimal(self):
        b = PresentationBuilder()
        theme = {"primary": "#1C2537", "accent": "#C4A962", "style": "minimal"}
        css = b.generate_variables_css(theme)
        assert "--pf-radius-lg" in css
