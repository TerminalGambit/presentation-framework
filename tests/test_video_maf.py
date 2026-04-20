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


class TestDegradation:
    """T3.5 — three graceful-degradation paths. Flag on and a video-maf
    slide, but the environment prevents a clean render; the build must
    still succeed (exit 0) with a warning and the template still produces
    an HTML slide via the poster fallback path."""

    def test_maf_not_on_path_degrades_to_poster(self, tmp_path, monkeypatch):
        """§5.1 — shutil.which("maf") returns None → warn + poster fallback."""
        # Strip PATH so nothing named `maf` resolves
        monkeypatch.setenv("PATH", "/no/such/path")
        cfg_path, metrics_path, _ = _write_deck(tmp_path, flag_on=True)

        # Boobytrap: subprocess.run must never be called when binary is missing.
        def fail_run(*a, **kw):  # pragma: no cover
            raise AssertionError("subprocess.run should not run when maf is absent")
        monkeypatch.setattr("subprocess.run", fail_run)

        builder, slides_dir = _build(tmp_path, cfg_path, metrics_path)
        data = builder.config["slides"][0]["data"]
        assert data.get("_maf_state") == "cold-cache-no-binary"
        assert "_mp4_path" not in data
        html = (slides_dir / "slide_01.html").read_text(encoding="utf-8")
        assert "<video" not in html
        assert any("maf binary" in w for w in getattr(builder, "_warnings", [])), (
            "a build warning should be recorded explaining the fallback"
        )

    def test_maf_nonzero_exit_degrades_with_stderr_preview(self, tmp_path, monkeypatch):
        """§5.2 — maf render exits non-zero → warn + poster fallback, exit 0."""
        # Install a fake maf that always exits 5 with a known stderr line
        bin_dir = tmp_path / "fakebin"
        bin_dir.mkdir()
        bad_maf = bin_dir / "maf"
        bad_maf.write_text(
            "#!/usr/bin/env bash\necho 'ERROR: render failed intentionally' >&2\nexit 5\n"
        )
        bad_maf.chmod(0o755)
        monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")

        cfg_path, metrics_path, _ = _write_deck(tmp_path, flag_on=True)
        builder, slides_dir = _build(tmp_path, cfg_path, metrics_path)
        data = builder.config["slides"][0]["data"]
        assert data.get("_maf_state") == "renderer-error"
        assert any("exited 5" in w for w in builder._warnings), (
            "warning should include the non-zero exit code"
        )
        assert any("render failed" in w for w in builder._warnings), (
            "stderr preview should be included in the warning"
        )
        html = (slides_dir / "slide_01.html").read_text(encoding="utf-8")
        assert "<video" not in html  # degraded to poster fallback

    def test_missing_manifest_fails_fast(self, tmp_path, monkeypatch):
        """§5.3 — manifest missing is a spec error; Click exception, not a
        warning. Build does not produce slide output."""
        import click
        # Put the stub on PATH so the only failure is the bogus manifest_path
        monkeypatch.setenv("PATH", f"{FIXTURE_DIR}{os.pathsep}{os.environ['PATH']}")

        # Write a deck that references a manifest that doesn't exist
        theme_cfg = {
            "primary": "#1C2537", "accent": "#C4A962",
            "fonts": {"heading": "PD", "subheading": "M", "body": "L", "mono": "IPM"},
            "experimental": {"maf_video": True},
        }
        config = {
            "meta": {"title": "Missing manifest"},
            "theme": theme_cfg,
            "slides": [
                {"layout": "video-maf", "data": {
                    "title": "Scene",
                    "manifest_path": "does-not-exist.maf.yaml",
                    "caption": "Will fail",
                }},
            ],
        }
        cfg = tmp_path / "presentation.yaml"
        cfg.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
        met = tmp_path / "metrics.json"
        met.write_text("{}")

        from pf.builder import PresentationBuilder
        with contextlib.chdir(tmp_path):
            builder = PresentationBuilder(config_path=str(cfg), metrics_path=str(met))
            with pytest.raises(click.ClickException) as excinfo:
                with contextlib.redirect_stdout(io.StringIO()):
                    builder.build(output_dir=str(tmp_path / "slides"))
        assert "manifest_path not found" in str(excinfo.value.message)


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


class TestCliIntegration:
    """Regression: `pf build` on a MAF slide where the binary is missing
    must not crash the CLI. The MAF degradation warnings are plain
    strings appended to builder._warnings; the CLI's post-build display
    loop is dict-shaped (overflow warnings) and must tolerate strings."""

    def test_cli_build_survives_maf_string_warning(self, tmp_path, monkeypatch):
        from click.testing import CliRunner
        from pf.cli import cli

        # Strip PATH so `maf` is not resolvable → triggers the string-warning path
        monkeypatch.setenv("PATH", "/no/such/dir")
        # Copy the stub manifest into a tmp deck
        manifest_src = FIXTURE_DIR / "manifest.maf.yaml"
        manifest_dst = tmp_path / "manifest.maf.yaml"
        manifest_dst.write_bytes(manifest_src.read_bytes())
        cfg_path, metrics_path, _ = _write_deck(tmp_path, flag_on=True)

        runner = CliRunner()
        with contextlib.chdir(tmp_path):
            result = runner.invoke(cli, [
                "build",
                "--config", str(cfg_path),
                "--metrics", str(metrics_path),
                "--output", str(tmp_path / "slides"),
            ])
        assert result.exit_code == 0, (
            f"pf build crashed on a MAF degradation warning: "
            f"exit={result.exit_code}, exc={result.exception}\noutput={result.output}"
        )
        assert "maf binary not on PATH" in result.output
        # Slide still written in degraded form
        assert (tmp_path / "slides" / "slide_01.html").exists()


class TestEndToEndCaching:
    """T3.6 — second build against a populated .pf-cache/maf/ cache hits
    the cache and skips the subprocess entirely (contract §3)."""

    def test_second_build_hits_cache_no_subprocess(self, tmp_path, monkeypatch):
        # First build: real subprocess against the stub binary
        monkeypatch.setenv("PATH", f"{FIXTURE_DIR}{os.pathsep}{os.environ['PATH']}")
        cfg_path, metrics_path, _ = _write_deck(tmp_path, flag_on=True)
        builder1, slides_dir1 = _build(tmp_path, cfg_path, metrics_path)
        assert builder1.config["slides"][0]["data"]["_maf_state"] == "rendered"
        cache_key = builder1.config["slides"][0]["data"]["_maf_cache_key"]
        cache_dir = tmp_path / ".pf-cache" / "maf" / cache_key
        assert (cache_dir / "scene.mp4").exists(), "first build should populate cache"
        assert (cache_dir / "render_result.json").exists()

        # Second build: boobytrap subprocess.run so any call fails the test.
        # A true cache hit must never invoke it.
        def fail(*a, **kw):  # pragma: no cover
            raise AssertionError("subprocess.run should NOT fire on a cache hit")
        monkeypatch.setattr("subprocess.run", fail)

        # Second builder instance, same config, same cache directory
        builder2, slides_dir2 = _build(tmp_path, cfg_path, metrics_path)
        data2 = builder2.config["slides"][0]["data"]
        assert data2["_maf_state"] == "rendered"
        assert data2["_maf_cache_key"] == cache_key
        # Artifacts still exist in the new slides dir (copied from cache)
        mp4_rel = data2["_mp4_path"]
        assert (slides_dir2 / mp4_rel).exists()
