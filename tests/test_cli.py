"""Tests for the pf plugins CLI command group.

Covers: plugins list, plugins install (success/failure), plugins info (not found),
and plugins --help.
"""

import sys
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from pf.cli import cli


def test_plugins_list():
    """pf plugins list exits 0 and shows the three section headers."""
    runner = CliRunner()
    result = runner.invoke(cli, ["plugins", "list"])
    assert result.exit_code == 0, result.output
    assert "Installed Plugins" in result.output
    assert "Layouts" in result.output
    assert "Themes" in result.output
    assert "Data Sources" in result.output


def test_plugins_install_calls_pip():
    """pf plugins install invokes sys.executable -m pip install <package>."""
    runner = CliRunner()

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    mock_result.stderr = ""

    with patch("subprocess.run", return_value=mock_result) as mock_run:
        result = runner.invoke(cli, ["plugins", "install", "pf-layout-test"])

    assert result.exit_code == 0, result.output
    mock_run.assert_called_once_with(
        [sys.executable, "-m", "pip", "install", "pf-layout-test"],
        capture_output=True,
        text=True,
    )
    assert "Installed pf-layout-test" in result.output


def test_plugins_install_failure():
    """pf plugins install exits non-zero and shows 'failed' message on pip error."""
    runner = CliRunner()

    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    mock_result.stderr = "ERROR: Could not find a version that satisfies the requirement nonexistent-pkg"

    with patch("subprocess.run", return_value=mock_result):
        result = runner.invoke(cli, ["plugins", "install", "nonexistent-pkg"])

    assert result.exit_code != 0
    # The failure message should mention the package name
    assert "Failed" in result.output or "nonexistent-pkg" in result.output


def test_plugins_info_not_found():
    """pf plugins info for an unknown plugin exits non-zero and reports not found."""
    runner = CliRunner()
    result = runner.invoke(cli, ["plugins", "info", "nonexistent-plugin-xyz"])
    assert result.exit_code != 0
    assert "not found" in result.output.lower() or "not found" in (result.output + "").lower()


def test_plugins_help():
    """pf plugins --help exits 0 and lists list, install, and info subcommands."""
    runner = CliRunner()
    result = runner.invoke(cli, ["plugins", "--help"])
    assert result.exit_code == 0, result.output
    assert "list" in result.output
    assert "install" in result.output
    assert "info" in result.output


# ── --base-url CLI tests ─────────────────────────────────────────

import json
import tempfile
from pathlib import Path

import yaml

_MINIMAL_CONFIG = {
    "meta": {"title": "CLI Base URL Test"},
    "theme": {
        "primary": "#1C2537",
        "accent": "#C4A962",
        "fonts": {
            "heading": "Playfair Display",
            "subheading": "Montserrat",
            "body": "Lato",
        },
    },
    "slides": [
        {"layout": "title", "data": {"title": "Hello"}},
        {"layout": "closing", "data": {"title": "Bye"}},
    ],
}


def _write_temp_project(tmpdir: Path) -> tuple[str, str, str]:
    """Write minimal config + metrics and return (config_path, metrics_path, out_dir)."""
    config_path = str(tmpdir / "presentation.yaml")
    metrics_path = str(tmpdir / "metrics.json")
    out_dir = str(tmpdir / "slides")
    (tmpdir / "presentation.yaml").write_text(
        yaml.dump(_MINIMAL_CONFIG), encoding="utf-8"
    )
    (tmpdir / "metrics.json").write_text("{}", encoding="utf-8")
    return config_path, metrics_path, out_dir


def test_build_base_url():
    """pf build --base-url produces HTML with absolute asset paths."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path, metrics_path, out_dir = _write_temp_project(Path(tmpdir))
        result = runner.invoke(
            cli,
            [
                "build",
                "-c", config_path,
                "-m", metrics_path,
                "-o", out_dir,
                "--base-url", "https://cdn.example.com",
            ],
        )
        assert result.exit_code == 0, result.output

        # Check that at least one HTML file has absolute theme paths
        slide_html = (Path(out_dir) / "slide_01.html").read_text(encoding="utf-8")
        assert "https://cdn.example.com/theme/" in slide_html


def test_build_no_base_url_default():
    """pf build without --base-url preserves relative paths."""
    runner = CliRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path, metrics_path, out_dir = _write_temp_project(Path(tmpdir))
        result = runner.invoke(
            cli,
            [
                "build",
                "-c", config_path,
                "-m", metrics_path,
                "-o", out_dir,
            ],
        )
        assert result.exit_code == 0, result.output

        slide_html = (Path(out_dir) / "slide_01.html").read_text(encoding="utf-8")
        # Relative reference must remain
        assert 'href="theme/variables.css"' in slide_html
        # No accidental CDN prefix
        assert "https://cdn.example.com" not in slide_html
