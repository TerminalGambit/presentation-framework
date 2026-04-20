"""T1.10 — Integration tests covering all built-in theme presets.

For each preset, this suite asserts:
  (a) the preset YAML loads (no parse errors, dict shape)
  (b) all required CSS custom properties appear in the generated CSS
  (c) check_contrast returns no warnings on examples/presentation.yaml
  (d) the screenshot returned by list_themes exists on disk

Plus one negative test: pf build with a non-existent preset raises a
helpful Click message that lists the available presets.
"""

from pathlib import Path

import click
import pytest
import yaml

from pf.builder import (
    PRESETS_DIR,
    PresentationBuilder,
    _list_presets,
    _load_preset,
)
from pf.contrast import check_contrast
from pf.mcp_server import list_themes

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_CONFIG = REPO_ROOT / "examples" / "presentation.yaml"
EXAMPLES_METRICS = REPO_ROOT / "examples" / "metrics.json"

REQUIRED_CSS_VARS = (
    "--pf-primary",
    "--pf-accent",
    "--pf-text",
    "--pf-contrast-text",
    "--pf-font-heading",
    "--pf-font-subheading",
    "--pf-font-body",
    "--pf-font-mono",
)

BUILTIN_PRESETS = ("default", "editorial", "terminal", "plex", "nord")


@pytest.fixture(scope="module")
def themes_index():
    """Index of preset name -> entry dict from list_themes()."""
    return {t["name"]: t for t in list_themes()}


@pytest.mark.parametrize("preset_name", BUILTIN_PRESETS)
class TestPreset:
    def test_yaml_loads(self, preset_name):
        data = _load_preset(preset_name)
        assert isinstance(data, dict)
        assert "primary" in data
        assert "accent" in data

    def test_required_css_vars_in_generated_css(self, preset_name):
        b = PresentationBuilder()
        css = b.generate_variables_css({"preset": preset_name})
        for var in REQUIRED_CSS_VARS:
            assert var in css, f"{preset_name}: missing CSS var {var}"

    def test_contrast_clean_on_examples_deck(self, preset_name, tmp_path):
        """Build examples deck with this preset and assert zero contrast warnings."""
        src = yaml.safe_load(EXAMPLES_CONFIG.read_text(encoding="utf-8"))
        src["theme"] = {"preset": preset_name, "math": True}
        cfg_path = tmp_path / "presentation.yaml"
        cfg_path.write_text(yaml.dump(src, sort_keys=False), encoding="utf-8")
        builder = PresentationBuilder(
            config_path=str(cfg_path),
            metrics_path=str(EXAMPLES_METRICS),
        )
        builder.build(output_dir=str(tmp_path / "slides"))
        assert builder._contrast_warnings == [], (
            f"{preset_name}: contrast warnings: {builder._contrast_warnings}"
        )

    def test_screenshot_exists_on_disk(self, preset_name, themes_index):
        entry = themes_index.get(preset_name)
        assert entry is not None, f"{preset_name} missing from list_themes()"
        screenshot = REPO_ROOT / entry["screenshot_path"]
        assert screenshot.is_file(), (
            f"{preset_name}: screenshot {entry['screenshot_path']} not on disk"
        )


def test_unknown_preset_raises_with_available_list():
    """Building with a non-existent preset surfaces a helpful error."""
    b = PresentationBuilder()
    with pytest.raises(click.ClickException) as exc:
        b.generate_variables_css({"preset": "definitely-not-a-real-preset"})
    msg = exc.value.message
    assert "definitely-not-a-real-preset" in msg
    # All built-in presets should be listed in the available list
    for builtin in BUILTIN_PRESETS:
        assert builtin in msg, f"Available list missing '{builtin}'"


def test_all_builtin_presets_discoverable():
    """_list_presets() should enumerate every built-in name."""
    discovered = set(_list_presets())
    for builtin in BUILTIN_PRESETS:
        assert builtin in discovered, f"_list_presets missing '{builtin}'"
