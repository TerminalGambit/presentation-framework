"""Tests for the MAF integration spike — contract docs/maf-integration-contract.md.

Covers:
- T3.4: flag-off entry guard; happy path against the stub binary.
- T3.5: graceful degradation (no binary, non-zero exit, missing manifest).
- T3.6: end-to-end build through the stub + cache-hit on second build.

None of these tests depend on a real MAF install. The
``tests/fixtures/video-maf-placeholder/maf`` shell script mimics the
subset of ``maf render`` that PF uses.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import yaml
from pathlib import Path
from unittest.mock import patch

import pytest


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "video-maf-placeholder"


def _write_deck(tmp_path, *, flag_on: bool, manifest_name: str = "manifest.maf.yaml",
                caption: str = "Stub clip") -> tuple[Path, Path, dict]:
    """Write a one-slide video-maf presentation + metrics to tmp_path and
    return (config_path, metrics_path, config_dict)."""
    # Copy the stub manifest next to the presentation YAML so relative path
    # resolution works the same as a real deck would.
    src_manifest = FIXTURE_DIR / "manifest.maf.yaml"
    dst_manifest = tmp_path / manifest_name
    dst_manifest.write_bytes(src_manifest.read_bytes())

    theme_cfg = {
        "primary": "#1C2537", "accent": "#C4A962",
        "fonts": {"heading": "PD", "subheading": "M", "body": "L", "mono": "IPM"},
    }
    if flag_on:
        theme_cfg["experimental"] = {"maf_video": True}
    config = {
        "meta": {"title": "MAF test"},
        "theme": theme_cfg,
        "slides": [
            {"layout": "video-maf", "data": {
                "title": "Scene 1",
                "manifest_path": manifest_name,
                "caption": caption,
            }},
        ],
    }
    cfg_path = tmp_path / "presentation.yaml"
    cfg_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    metrics_path = tmp_path / "metrics.json"
    metrics_path.write_text(json.dumps({}), encoding="utf-8")
    return cfg_path, metrics_path, config


def _build(tmp_path, cfg_path, metrics_path):
    """Run the builder in tmp_path; return (builder, slides_dir_path)."""
    from pf.builder import PresentationBuilder
    with contextlib.chdir(tmp_path):
        builder = PresentationBuilder(
            config_path=str(cfg_path), metrics_path=str(metrics_path)
        )
        with contextlib.redirect_stdout(io.StringIO()):
            out = builder.build(output_dir=str(tmp_path / "slides"))
    return builder, out


class TestFlagGate:
    """T3.4 — entry-point check: when the flag is off, the subprocess path
    is not entered under any circumstances."""

    def test_flag_off_no_subprocess(self, tmp_path):
        """If subprocess.run were called, this boobytrap raises — so the
        assertion is that the build completes without touching it."""
        cfg_path, metrics_path, _ = _write_deck(tmp_path, flag_on=False)

        def fail(*a, **kw):  # pragma: no cover — should never fire
            raise AssertionError("subprocess.run must NOT be called when flag is off")

        # _build_maf_video does `import subprocess` lazily inside the
        # method, so patching subprocess.run at the module level still
        # catches any accidental invocation.
        with patch("subprocess.run", side_effect=fail):
            builder, slides_dir = _build(tmp_path, cfg_path, metrics_path)

        data = builder.config["slides"][0]["data"]
        assert data.get("_maf_state") == "flag-off"
        assert "_mp4_path" not in data
        # Slide HTML renders without a <video> element (poster path).
        slide_html = (slides_dir / "slide_01.html").read_text(encoding="utf-8")
        assert "<video" not in slide_html
        assert "Stub clip" in slide_html  # caption still rendered


class TestHappyPathWithStub:
    """T3.4 — flag on + stub binary on PATH → slide renders a real <video>
    with the embedded mp4 path."""

    def test_flag_on_with_stub(self, tmp_path, monkeypatch):
        monkeypatch.setenv("PATH", f"{FIXTURE_DIR}{os.pathsep}{os.environ['PATH']}")
        cfg_path, metrics_path, _ = _write_deck(tmp_path, flag_on=True)
        builder, slides_dir = _build(tmp_path, cfg_path, metrics_path)

        data = builder.config["slides"][0]["data"]
        assert data.get("_maf_state") == "rendered"
        mp4_rel = data.get("_mp4_path")
        assert mp4_rel and mp4_rel.endswith("scene.mp4")
        assert (slides_dir / mp4_rel).exists(), "mp4 should be copied into slides dir"
        # VTT caption track is emitted by the stub → should be wired into HTML
        assert data.get("_vtt_path", "").endswith("scene.vtt")

        html = (slides_dir / "slide_01.html").read_text(encoding="utf-8")
        assert "<video" in html
        assert mp4_rel in html
        assert "<track" in html
