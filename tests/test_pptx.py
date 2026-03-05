"""Tests for pf.pptx PowerPoint export."""

import pytest
from pathlib import Path


class TestPptxImport:
    def test_pptx_module_exists(self):
        from pf import pptx
        assert hasattr(pptx, "export_pptx")

    def test_pptx_graceful_without_playwright(self, monkeypatch):
        """If Playwright is missing, export_pptx raises ImportError."""
        import pf.pptx as pptx_mod
        monkeypatch.setattr(pptx_mod, "PLAYWRIGHT_AVAILABLE", False)
        with pytest.raises(ImportError, match="Playwright"):
            pptx_mod.export_pptx("fake_dir", "out.pptx")

    def test_pptx_no_slides_raises(self, tmp_path):
        """If slides dir has no slide_*.html, raise FileNotFoundError."""
        from pf.pptx import export_pptx
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        with pytest.raises(FileNotFoundError, match="No slide files"):
            export_pptx(str(empty_dir), str(tmp_path / "out.pptx"))


class TestPptxCli:
    def test_pptx_command_exists(self):
        from click.testing import CliRunner
        from pf.cli import cli
        runner = CliRunner()
        result = runner.invoke(cli, ["pptx", "--help"])
        assert result.exit_code == 0
        assert "PowerPoint" in result.output or "pptx" in result.output.lower()

    def test_pptx_missing_config(self):
        from click.testing import CliRunner
        from pf.cli import cli
        runner = CliRunner()
        result = runner.invoke(cli, ["pptx", "-c", "/nonexistent/config.yaml"])
        assert result.exit_code != 0
