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


class TestPDFSentinelWait:
    """PDF export waits for data-pf-ready sentinel (EXPORT-01)."""

    def test_pdf_code_references_sentinel(self):
        from pathlib import Path
        code = (Path(__file__).parent.parent / "pf" / "pdf.py").read_text()
        assert "data-pf-ready" in code, "pdf.py should wait for data-pf-ready sentinel"


class TestPDFNotesSupport:
    """PDF export supports include_notes parameter (EXPORT-03)."""

    def test_export_pdf_accepts_include_notes(self):
        """Verify export_pdf signature includes include_notes."""
        import inspect
        from pf.pdf import export_pdf
        sig = inspect.signature(export_pdf)
        assert "include_notes" in sig.parameters

    def test_export_pdf_accepts_config(self):
        """Verify export_pdf signature includes config parameter for notes."""
        import inspect
        from pf.pdf import export_pdf
        sig = inspect.signature(export_pdf)
        assert "config" in sig.parameters

    def test_render_notes_page_returns_html(self):
        """_render_notes_page generates valid HTML with slide data."""
        from pf.pdf import _render_notes_page
        html = _render_notes_page("My Slide Title", "Speaker note text here.", 3)
        assert "My Slide Title" in html
        assert "Speaker note text here." in html
        assert "SLIDE 03" in html
        assert "<!DOCTYPE html>" in html
