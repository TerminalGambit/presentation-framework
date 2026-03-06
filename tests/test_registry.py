"""Tests for pf.registry.PluginRegistry and related plugin dataclasses."""

import json
import warnings
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml
from jinja2 import ChoiceLoader

from pf.builder import PresentationBuilder
from pf.registry import (
    DataSourcePlugin,
    LayoutPlugin,
    LocalLayoutPlugin,
    PluginCredentialError,
    PluginRegistry,
    ThemePlugin,
)


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


THEME_BASE = {
    "primary": "#1C2537",
    "accent": "#C4A962",
    "fonts": {
        "heading": "Playfair Display",
        "subheading": "Montserrat",
        "body": "Lato",
    },
}


@pytest.fixture
def registry():
    return PluginRegistry()


# ---------------------------------------------------------------------------
# 1. Entry-point layout discovery
# ---------------------------------------------------------------------------


class TestLayoutDiscoveryViaEntryPoints:
    def test_layout_discovery_via_entry_points(self, registry):
        """A LayoutPlugin exposed via pf.layouts entry point appears in layout_names."""
        fake_plugin = LayoutPlugin(name="fancy-grid", description="A fancy grid layout")

        fake_ep = MagicMock()
        fake_ep.name = "fancy-grid"
        fake_ep.load.return_value = fake_plugin

        with patch("pf.registry.entry_points") as mock_eps:
            mock_eps.side_effect = lambda group: (
                [fake_ep] if group == "pf.layouts" else []
            )
            registry.discover()

        assert "fancy-grid" in registry.layout_names

    def test_entry_point_plugin_stored_as_layout_plugin(self, registry):
        """The stored object is the LayoutPlugin instance from the entry point."""
        fake_plugin = LayoutPlugin(
            name="kanban",
            description="Kanban board layout",
            version="1.0.0",
        )
        fake_ep = MagicMock()
        fake_ep.name = "kanban"
        fake_ep.load.return_value = fake_plugin

        with patch("pf.registry.entry_points") as mock_eps:
            mock_eps.side_effect = lambda group: (
                [fake_ep] if group == "pf.layouts" else []
            )
            registry.discover()

        stored = registry.get_layout("kanban")
        assert stored is fake_plugin
        assert stored.version == "1.0.0"


# ---------------------------------------------------------------------------
# 2. Local directory discovery
# ---------------------------------------------------------------------------


class TestLocalDirectoryDiscovery:
    def test_local_directory_discovery(self, registry, tmp_path):
        """Templates in <project>/layouts/ are discovered as LocalLayoutPlugins."""
        layouts_dir = tmp_path / "layouts"
        layouts_dir.mkdir()
        (layouts_dir / "custom.html.j2").write_text(
            "<div>{{ slide.data.title }}</div>", encoding="utf-8"
        )

        registry.discover(project_dir=tmp_path)

        assert "custom" in registry.layout_names

    def test_local_layout_is_local_layout_plugin(self, registry, tmp_path):
        """Local templates produce LocalLayoutPlugin instances."""
        layouts_dir = tmp_path / "layouts"
        layouts_dir.mkdir()
        (layouts_dir / "kanban.html.j2").write_text("<div>kanban</div>", encoding="utf-8")

        registry.discover(project_dir=tmp_path)

        stored = registry.get_layout("kanban")
        assert isinstance(stored, LocalLayoutPlugin)
        assert stored.name == "kanban"
        assert stored.template_path.name == "kanban.html.j2"

    def test_multiple_local_templates(self, registry, tmp_path):
        """All *.html.j2 files in layouts/ are discovered."""
        layouts_dir = tmp_path / "layouts"
        layouts_dir.mkdir()
        for name in ["alpha", "beta", "gamma"]:
            (layouts_dir / f"{name}.html.j2").write_text(f"<div>{name}</div>", encoding="utf-8")

        registry.discover(project_dir=tmp_path)

        for name in ["alpha", "beta", "gamma"]:
            assert name in registry.layout_names

    def test_no_layouts_dir_is_safe(self, registry, tmp_path):
        """discover() with a project_dir that has no layouts/ subdirectory is safe."""
        registry.discover(project_dir=tmp_path)
        assert registry.layout_names == []


# ---------------------------------------------------------------------------
# 3. Builder uses ChoiceLoader
# ---------------------------------------------------------------------------


class TestBuilderUsesChoiceLoader:
    def test_builder_uses_choice_loader(self, tmp_path):
        """PresentationBuilder.env.loader should be a ChoiceLoader."""
        config = {
            "meta": {"title": "Test"},
            "theme": THEME_BASE,
            "slides": [{"layout": "title", "data": {"title": "Hi"}}],
        }
        config_path = tmp_path / "presentation.yaml"
        config_path.write_text(yaml.dump(config), encoding="utf-8")
        metrics_path = tmp_path / "metrics.json"
        metrics_path.write_text(json.dumps({}), encoding="utf-8")

        builder = PresentationBuilder(str(config_path), str(metrics_path))

        assert isinstance(builder.env.loader, ChoiceLoader)

    def test_choice_loader_has_core_loader(self, tmp_path):
        """ChoiceLoader contains at least one FileSystemLoader pointing to core templates."""
        config_path = tmp_path / "presentation.yaml"
        config_path.write_text(yaml.dump({"slides": []}), encoding="utf-8")
        metrics_path = tmp_path / "metrics.json"
        metrics_path.write_text("{}", encoding="utf-8")

        builder = PresentationBuilder(str(config_path), str(metrics_path))

        from jinja2 import FileSystemLoader

        loaders = builder.env.loader.loaders
        assert any(isinstance(ldr, FileSystemLoader) for ldr in loaders)


# ---------------------------------------------------------------------------
# 4. Empty registry on clean install
# ---------------------------------------------------------------------------


class TestRegistryEmptyOnCleanInstall:
    def test_registry_empty_on_clean_install(self, registry):
        """With no entry points and no local dirs, all name lists are empty."""
        with patch("pf.registry.entry_points", return_value=[]):
            registry.discover()

        assert registry.layout_names == []
        assert registry.theme_names == []
        assert registry.datasource_names == []


# ---------------------------------------------------------------------------
# 5. LocalLayoutPlugin creation
# ---------------------------------------------------------------------------


class TestLocalLayoutPluginCreation:
    def test_local_layout_plugin_creation(self, tmp_path):
        """Verify LocalLayoutPlugin is created with correct name and path."""
        layouts_dir = tmp_path / "layouts"
        layouts_dir.mkdir()
        tpl_path = layouts_dir / "swimlane.html.j2"
        tpl_path.write_text("<div>swimlane</div>", encoding="utf-8")

        plugin = LocalLayoutPlugin(name="swimlane", template_path=tpl_path)

        assert plugin.name == "swimlane"
        assert plugin.template_path == tpl_path
        assert plugin.template_path.exists()

    def test_name_derived_from_filename(self, registry, tmp_path):
        """Name is derived by stripping .html.j2 from the filename."""
        layouts_dir = tmp_path / "layouts"
        layouts_dir.mkdir()
        (layouts_dir / "cool-layout.html.j2").write_text("<div></div>", encoding="utf-8")

        registry.discover(project_dir=tmp_path)

        assert "cool-layout" in registry.layout_names
        assert "cool-layout.html" not in registry.layout_names


# ---------------------------------------------------------------------------
# 6. Broken plugin emits warning
# ---------------------------------------------------------------------------


class TestBrokenPluginEmitsWarning:
    def test_broken_plugin_emits_warning(self, registry):
        """An entry point whose .load() raises ImportError emits a warning and is skipped."""
        bad_ep = MagicMock()
        bad_ep.name = "broken-plugin"
        bad_ep.load.side_effect = ImportError("missing dependency")

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            with patch("pf.registry.entry_points") as mock_eps:
                mock_eps.side_effect = lambda group: (
                    [bad_ep] if group == "pf.layouts" else []
                )
                registry.discover()

        assert any("broken-plugin" in str(w.message) for w in caught)
        assert "broken-plugin" not in registry.layout_names

    def test_broken_plugin_does_not_crash_registry(self, registry):
        """Registry remains functional after a broken entry point is encountered."""
        good_ep = MagicMock()
        good_ep.name = "good-layout"
        good_ep.load.return_value = LayoutPlugin(name="good-layout")

        bad_ep = MagicMock()
        bad_ep.name = "bad-layout"
        bad_ep.load.side_effect = RuntimeError("broken")

        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            with patch("pf.registry.entry_points") as mock_eps:
                mock_eps.side_effect = lambda group: (
                    [good_ep, bad_ep] if group == "pf.layouts" else []
                )
                registry.discover()

        assert "good-layout" in registry.layout_names
        assert "bad-layout" not in registry.layout_names


# ---------------------------------------------------------------------------
# 7. Backward compatibility — no registry argument
# ---------------------------------------------------------------------------


class TestBackwardCompatibilityNoRegistry:
    def test_backward_compatibility_no_registry(self, tmp_path):
        """PresentationBuilder without explicit registry creates its own and renders core layouts."""
        config = {
            "meta": {"title": "Compat Test"},
            "theme": THEME_BASE,
            "slides": [
                {
                    "layout": "title",
                    "data": {
                        "title": "Backward Compatible",
                        "subtitle": "No registry arg",
                    },
                }
            ],
        }
        config_path = tmp_path / "presentation.yaml"
        config_path.write_text(yaml.dump(config), encoding="utf-8")
        metrics_path = tmp_path / "metrics.json"
        metrics_path.write_text(json.dumps({}), encoding="utf-8")

        # Build without passing registry — should succeed
        builder = PresentationBuilder(str(config_path), str(metrics_path))
        output_dir = tmp_path / "slides"
        output = builder.build(str(output_dir))

        assert output.exists()
        slide_file = output / "slide_01.html"
        assert slide_file.exists()
        html = slide_file.read_text(encoding="utf-8")
        assert "Backward Compatible" in html

    def test_builder_has_internal_registry(self, tmp_path):
        """Builder always exposes a _registry attribute (even without explicit arg)."""
        config_path = tmp_path / "presentation.yaml"
        config_path.write_text(yaml.dump({"slides": []}), encoding="utf-8")

        builder = PresentationBuilder(str(config_path))

        assert hasattr(builder, "_registry")
        assert isinstance(builder._registry, PluginRegistry)


# ---------------------------------------------------------------------------
# 8. Schema accepts plugin layout names
# ---------------------------------------------------------------------------


class TestSchemaAcceptsPluginLayoutName:
    def test_schema_accepts_plugin_layout_name(self):
        """Schema validates successfully when layout is a custom plugin name."""
        import json as _json
        from pathlib import Path as _Path

        schema_path = _Path(__file__).parent.parent / "pf" / "schema.json"
        import jsonschema

        with open(schema_path, "r", encoding="utf-8") as f:
            schema = _json.load(f)

        config = {
            "slides": [{"layout": "custom-plugin", "data": {"title": "Test"}}]
        }
        validator = jsonschema.Draft202012Validator(schema)
        errors = list(validator.iter_errors(config))
        assert errors == [], f"Unexpected validation errors: {errors}"

    def test_schema_rejects_non_string_layout(self):
        """Schema still rejects non-string layout values (type check preserved)."""
        import json as _json
        from pathlib import Path as _Path

        schema_path = _Path(__file__).parent.parent / "pf" / "schema.json"
        import jsonschema

        with open(schema_path, "r", encoding="utf-8") as f:
            schema = _json.load(f)

        config = {
            "slides": [{"layout": 42, "data": {"title": "Test"}}]
        }
        validator = jsonschema.Draft202012Validator(schema)
        errors = list(validator.iter_errors(config))
        assert len(errors) > 0


# ---------------------------------------------------------------------------
# Exports smoke test
# ---------------------------------------------------------------------------


class TestPluginDataclasses:
    def test_all_exports_importable(self):
        """All documented exports can be imported from pf.registry."""
        from pf.registry import (  # noqa: F401
            DataSourcePlugin,
            LayoutPlugin,
            LocalLayoutPlugin,
            PluginCredentialError,
            PluginRegistry,
            ThemePlugin,
        )

    def test_plugin_credential_error_is_exception(self):
        with pytest.raises(PluginCredentialError):
            raise PluginCredentialError("missing API key")

    def test_layout_plugin_defaults(self):
        p = LayoutPlugin(name="test")
        assert p.description == ""
        assert p.templates_dir is None
        assert p.css_files == []
        assert p.version == "0.0.0"

    def test_theme_plugin_defaults(self):
        t = ThemePlugin(name="dark-mode")
        assert t.defaults == {}
        assert t.css_file is None
        assert t.version == "0.0.0"

    def test_datasource_plugin_defaults(self):
        d = DataSourcePlugin(name="sheets")
        assert d.fetch_fn is None
        assert d.version == "0.0.0"


# ---------------------------------------------------------------------------
# 9. Theme plugin discovery and merge
# ---------------------------------------------------------------------------


class TestThemePluginDiscovery:
    def test_theme_discovery_via_entry_points(self, registry):
        """A ThemePlugin exposed via pf.themes entry point appears in theme_names."""
        fake_plugin = ThemePlugin(
            name="corporate",
            defaults={"primary": "#003366", "accent": "#FFD700", "fonts": {"heading": "Arial"}},
        )
        fake_ep = MagicMock()
        fake_ep.name = "corporate"
        fake_ep.load.return_value = fake_plugin

        with patch("pf.registry.entry_points") as mock_eps:
            mock_eps.side_effect = lambda group: (
                [fake_ep] if group == "pf.themes" else []
            )
            registry.discover()

        assert "corporate" in registry.theme_names
        assert registry.get_theme("corporate").defaults["primary"] == "#003366"

    def test_theme_plugin_merge(self, tmp_path):
        """Plugin defaults merged with user overrides: user values win, fonts deep-merged."""
        fake_plugin = ThemePlugin(
            name="corporate",
            defaults={
                "primary": "#003366",
                "accent": "#FFD700",
                "style": "bold",
                "fonts": {"heading": "Arial", "body": "Helvetica"},
            },
        )
        fake_ep = MagicMock()
        fake_ep.name = "corporate"
        fake_ep.load.return_value = fake_plugin

        # presentation.yaml with theme.name and partial overrides
        config = {
            "meta": {"title": "Theme Merge Test"},
            "theme": {
                "name": "corporate",
                "accent": "#FF0000",  # override
                "fonts": {"heading": "Custom Font"},  # partial font override
            },
            "slides": [{"layout": "title", "data": {"title": "Merge Test"}}],
        }
        config_path = tmp_path / "presentation.yaml"
        config_path.write_text(yaml.dump(config), encoding="utf-8")
        metrics_path = tmp_path / "metrics.json"
        metrics_path.write_text("{}", encoding="utf-8")

        pre_loaded_registry = PluginRegistry()
        with patch("pf.registry.entry_points") as mock_eps:
            mock_eps.side_effect = lambda group: (
                [fake_ep] if group == "pf.themes" else []
            )
            pre_loaded_registry.discover()

        builder = PresentationBuilder(
            str(config_path), str(metrics_path), registry=pre_loaded_registry
        )
        output_dir = tmp_path / "slides"
        builder.build(str(output_dir))

        css = (output_dir / "theme" / "variables.css").read_text(encoding="utf-8")

        # Primary comes from plugin default (user did not override)
        assert "#003366" in css
        # Accent comes from user override
        assert "#FF0000" in css.lower() or "#ff0000" in css.lower()
        # Plugin default accent is NOT used
        assert "#FFD700" not in css and "#ffd700" not in css.lower()
        # Font heading overridden by user
        assert "Custom Font" in css
        # Font body from plugin default (user didn't override)
        assert "Helvetica" in css

    def test_theme_no_name_key_uses_inline(self, tmp_path):
        """When theme has no 'name' key, inline values are used directly (no plugin merge)."""
        config = {
            "meta": {"title": "Inline Theme Test"},
            "theme": {
                "primary": "#111111",
                "accent": "#AAAAAA",
                "fonts": {"heading": "Arial", "subheading": "Helvetica", "body": "Lato"},
            },
            "slides": [{"layout": "title", "data": {"title": "Inline"}}],
        }
        config_path = tmp_path / "presentation.yaml"
        config_path.write_text(yaml.dump(config), encoding="utf-8")
        metrics_path = tmp_path / "metrics.json"
        metrics_path.write_text("{}", encoding="utf-8")

        builder = PresentationBuilder(str(config_path), str(metrics_path))
        output_dir = tmp_path / "slides"
        builder.build(str(output_dir))

        css = (output_dir / "theme" / "variables.css").read_text(encoding="utf-8")
        assert "#111111" in css

    def test_theme_unknown_name_ignored(self, tmp_path):
        """An unknown theme name silently falls back to inline values."""
        config = {
            "meta": {"title": "Unknown Theme Test"},
            "theme": {
                "name": "nonexistent",
                "primary": "#222222",
                "accent": "#BBBBBB",
                "fonts": {"heading": "Arial", "subheading": "Helvetica", "body": "Lato"},
            },
            "slides": [{"layout": "title", "data": {"title": "Unknown Theme"}}],
        }
        config_path = tmp_path / "presentation.yaml"
        config_path.write_text(yaml.dump(config), encoding="utf-8")
        metrics_path = tmp_path / "metrics.json"
        metrics_path.write_text("{}", encoding="utf-8")

        builder = PresentationBuilder(str(config_path), str(metrics_path))
        output_dir = tmp_path / "slides"
        # Should not raise — unknown theme name is silently ignored
        builder.build(str(output_dir))

        css = (output_dir / "theme" / "variables.css").read_text(encoding="utf-8")
        assert "#222222" in css

    def test_schema_accepts_theme_name(self):
        """Validate that a config with theme.name passes schema validation."""
        import json as _json
        from pathlib import Path as _Path

        import jsonschema

        schema_path = _Path(__file__).parent.parent / "pf" / "schema.json"
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = _json.load(f)

        config = {
            "slides": [{"layout": "title", "data": {"title": "Test"}}],
            "theme": {"name": "test-theme"},
        }
        validator = jsonschema.Draft202012Validator(schema)
        errors = list(validator.iter_errors(config))
        assert errors == [], f"Unexpected validation errors: {errors}"


# ---------------------------------------------------------------------------
# 10. Template inheritance via ChoiceLoader
# ---------------------------------------------------------------------------


class TestTemplateInheritance:
    def test_template_inheritance(self, tmp_path):
        """A local plugin template that extends base.html.j2 renders its content block."""
        layouts_dir = tmp_path / "layouts"
        layouts_dir.mkdir()
        (layouts_dir / "variant.html.j2").write_text(
            '{% extends "base.html.j2" %}'
            "{% block content %}<div>VARIANT CONTENT</div>{% endblock %}",
            encoding="utf-8",
        )

        config = {
            "meta": {"title": "Inheritance Test"},
            "theme": THEME_BASE,
            "slides": [{"layout": "variant", "data": {"title": "Variant Slide"}}],
        }
        config_path = tmp_path / "presentation.yaml"
        config_path.write_text(yaml.dump(config), encoding="utf-8")
        metrics_path = tmp_path / "metrics.json"
        metrics_path.write_text(json.dumps({}), encoding="utf-8")

        builder = PresentationBuilder(str(config_path), str(metrics_path))
        output_dir = tmp_path / "slides"
        builder.build(str(output_dir))

        slide_html = (output_dir / "slide_01.html").read_text(encoding="utf-8")
        # Plugin content block rendered
        assert "VARIANT CONTENT" in slide_html
        # Inheritance from base.html.j2 worked — base scaffold is present
        assert "<!DOCTYPE html>" in slide_html
        assert "theme/variables.css" in slide_html


# ---------------------------------------------------------------------------
# 11. CSS injection into output directory
# ---------------------------------------------------------------------------


class TestCSSInjection:
    def test_css_injection(self, tmp_path):
        """Plugin CSS is copied to theme/plugins/ and linked in slide HTML."""
        layouts_dir = tmp_path / "layouts"
        layouts_dir.mkdir()
        (layouts_dir / "testlayout.html.j2").write_text(
            '{% extends "base.html.j2" %}'
            '{% block content %}<div class="pf-layout-testlayout">TEST</div>{% endblock %}',
            encoding="utf-8",
        )
        (layouts_dir / "testlayout.css").write_text(
            ".pf-layout-testlayout { color: red; }",
            encoding="utf-8",
        )

        config = {
            "meta": {"title": "CSS Injection Test"},
            "theme": THEME_BASE,
            "slides": [{"layout": "testlayout", "data": {"title": "Test Slide"}}],
        }
        config_path = tmp_path / "presentation.yaml"
        config_path.write_text(yaml.dump(config), encoding="utf-8")
        metrics_path = tmp_path / "metrics.json"
        metrics_path.write_text(json.dumps({}), encoding="utf-8")

        builder = PresentationBuilder(str(config_path), str(metrics_path))
        output_dir = tmp_path / "slides"
        builder.build(str(output_dir))

        # CSS file was copied to theme/plugins/
        copied_css = output_dir / "theme" / "plugins" / "testlayout.css"
        assert copied_css.exists(), "Plugin CSS not copied to theme/plugins/"
        assert ".pf-layout-testlayout" in copied_css.read_text(encoding="utf-8")

        # CSS link is present in the rendered slide HTML
        slide_html = (output_dir / "slide_01.html").read_text(encoding="utf-8")
        assert "theme/plugins/testlayout.css" in slide_html


# ---------------------------------------------------------------------------
# 12. CSS isolation — plugin CSS available but scoped via class prefix
# ---------------------------------------------------------------------------


class TestCSSIsolation:
    def test_css_isolation(self, tmp_path):
        """Plugin CSS class prefix appears in plugin slide; core title slide is unaffected."""
        layouts_dir = tmp_path / "layouts"
        layouts_dir.mkdir()
        (layouts_dir / "myplugin.html.j2").write_text(
            '{% extends "base.html.j2" %}'
            '{% block content %}'
            '<div class="pf-layout-myplugin">PLUGIN SLIDE</div>'
            "{% endblock %}",
            encoding="utf-8",
        )
        (layouts_dir / "myplugin.css").write_text(
            ".pf-layout-myplugin { background: navy; }",
            encoding="utf-8",
        )

        config = {
            "meta": {"title": "Isolation Test"},
            "theme": THEME_BASE,
            "slides": [
                {"layout": "title", "data": {"title": "Core Title Slide"}},
                {"layout": "myplugin", "data": {"title": "Plugin Slide"}},
            ],
        }
        config_path = tmp_path / "presentation.yaml"
        config_path.write_text(yaml.dump(config), encoding="utf-8")
        metrics_path = tmp_path / "metrics.json"
        metrics_path.write_text(json.dumps({}), encoding="utf-8")

        builder = PresentationBuilder(str(config_path), str(metrics_path))
        output_dir = tmp_path / "slides"
        builder.build(str(output_dir))

        title_html = (output_dir / "slide_01.html").read_text(encoding="utf-8")
        plugin_html = (output_dir / "slide_02.html").read_text(encoding="utf-8")

        # Title slide does NOT contain plugin-specific CSS class in its content
        assert "pf-layout-myplugin" not in title_html
        # Plugin slide DOES contain the plugin CSS class wrapper
        assert "pf-layout-myplugin" in plugin_html
        # Both slides link the same plugin CSS file (shared, but scoped by class prefix)
        assert "theme/plugins/myplugin.css" in title_html
        assert "theme/plugins/myplugin.css" in plugin_html


# ---------------------------------------------------------------------------
# 13. No plugin CSS when no plugins present
# ---------------------------------------------------------------------------


class TestNoPluginCSSWhenNoPlugins:
    def test_no_plugin_css_when_no_plugins(self, tmp_path):
        """Standard build with no plugins does not create theme/plugins/ directory."""
        config = {
            "meta": {"title": "No Plugins Test"},
            "theme": THEME_BASE,
            "slides": [{"layout": "title", "data": {"title": "Core Only"}}],
        }
        config_path = tmp_path / "presentation.yaml"
        config_path.write_text(yaml.dump(config), encoding="utf-8")
        metrics_path = tmp_path / "metrics.json"
        metrics_path.write_text(json.dumps({}), encoding="utf-8")

        builder = PresentationBuilder(str(config_path), str(metrics_path))
        output_dir = tmp_path / "slides"
        builder.build(str(output_dir))

        plugins_dir = output_dir / "theme" / "plugins"
        assert not plugins_dir.exists(), (
            "theme/plugins/ directory should not exist when no plugins are present"
        )
