"""Tests for python -m pf entry point."""
import subprocess
import sys


def test_module_invocation_shows_help():
    """python3 -m pf --help should print usage and exit 0."""
    result = subprocess.run(
        [sys.executable, "-m", "pf", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Usage" in result.stdout


def test_module_invocation_build_missing_config():
    """python3 -m pf build with no config should fail with a clear error."""
    result = subprocess.run(
        [sys.executable, "-m", "pf", "build", "--config", "nonexistent.yaml"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
