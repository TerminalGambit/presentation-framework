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
