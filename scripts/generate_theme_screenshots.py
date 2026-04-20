#!/usr/bin/env python3
"""Generate per-preset screenshots used by the MCP `list_themes` tool.

For each built-in preset, build `examples/presentation.yaml` with that
preset overlaid into a tmpdir, then capture `slide_01.html` at 1280x720
and write `docs/themes/<preset>.png`.

Run from the repo root:
    python3 scripts/generate_theme_screenshots.py
"""

import sys
import tempfile
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent

# Make `pf` importable when running from a fresh checkout
sys.path.insert(0, str(REPO_ROOT))

from pf.builder import PRESETS_DIR, PresentationBuilder  # noqa: E402

EXAMPLES_CONFIG = REPO_ROOT / "examples" / "presentation.yaml"
EXAMPLES_METRICS = REPO_ROOT / "examples" / "metrics.json"
SCREENSHOTS_DIR = REPO_ROOT / "docs" / "themes"


def list_preset_names() -> list[str]:
    if not PRESETS_DIR.is_dir():
        return []
    return sorted(p.stem for p in PRESETS_DIR.glob("*.yaml"))


def capture_first_slide(slides_dir: Path, out_png: Path, browser_context) -> None:
    page = browser_context.new_page()
    try:
        page.goto(f"file://{(slides_dir / 'slide_01.html').resolve()}")
        page.wait_for_load_state("networkidle")
        try:
            page.wait_for_selector("[data-pf-ready]", timeout=10000)
        except Exception:
            pass
        page.screenshot(path=str(out_png), full_page=False)
    finally:
        page.close()


def build_preset_to_dir(preset_name: str, build_dir: Path) -> Path:
    src = yaml.safe_load(EXAMPLES_CONFIG.read_text(encoding="utf-8"))
    src["theme"] = {"preset": preset_name, "math": True}
    cfg_path = build_dir / "presentation.yaml"
    cfg_path.write_text(yaml.dump(src, sort_keys=False), encoding="utf-8")
    out = build_dir / "slides"
    builder = PresentationBuilder(
        config_path=str(cfg_path),
        metrics_path=str(EXAMPLES_METRICS),
    )
    builder.build(output_dir=str(out))
    return out


def main() -> int:
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    presets = list_preset_names()
    if not presets:
        print("ERROR: no presets found under theme/presets/", file=sys.stderr)
        return 1

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print(
            "ERROR: Playwright is required. Install with `pip install playwright && playwright install chromium`",
            file=sys.stderr,
        )
        return 1

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        try:
            for preset in presets:
                print(f"  → {preset}")
                with tempfile.TemporaryDirectory() as tmp:
                    slides_dir = build_preset_to_dir(preset, Path(tmp))
                    out_png = SCREENSHOTS_DIR / f"{preset}.png"
                    capture_first_slide(slides_dir, out_png, context)
        finally:
            context.close()
            browser.close()

    print(f"Wrote {len(presets)} screenshots to {SCREENSHOTS_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
