"""Tests for PDF export."""

import pytest


class TestPdfImport:
    def test_pdf_module_exists(self):
        from pf.pdf import export_pdf
        assert callable(export_pdf)

    def test_pdf_graceful_without_playwright(self, monkeypatch):
        """If playwright is not installed, should raise ImportError with helpful message."""
        import pf.pdf
        monkeypatch.setattr(pf.pdf, "PLAYWRIGHT_AVAILABLE", False)
        with pytest.raises(ImportError, match="pip install"):
            pf.pdf.export_pdf("slides/", "output.pdf")


class TestPdfCli:
    def test_pdf_command_exists(self):
        from click.testing import CliRunner
        from pf.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["pdf", "--help"])
        assert result.exit_code == 0
        assert "Export" in result.output or "PDF" in result.output

    def test_pdf_missing_config(self):
        from click.testing import CliRunner
        from pf.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["pdf", "-c", "nonexistent.yaml"])
        assert result.exit_code != 0

    def test_pdf_no_slides_found(self, tmp_path, monkeypatch):
        """export_pdf should raise FileNotFoundError if no slide files exist."""
        import pf.pdf
        monkeypatch.setattr(pf.pdf, "PLAYWRIGHT_AVAILABLE", True)
        # Mock sync_playwright so we don't need actual Playwright installed
        with pytest.raises(FileNotFoundError, match="No slide files"):
            pf.pdf.export_pdf(str(tmp_path), "output.pdf")
