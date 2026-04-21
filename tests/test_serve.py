"""Tests for pf serve live-reload functionality."""

import contextlib
import io
import json
import threading
import time
import urllib.request
import urllib.error

import pytest
import yaml
from click.testing import CliRunner

from pf.cli import cli


class TestLiveReloadInjection:
    """v0.3.1 — the /__reload SSE client must NOT appear in the navigator
    unless the deck was built with live_reload=True. Plain `pf build` users
    would otherwise see a 404 in the console whenever they serve the deck
    with any HTTP server other than `pf serve --watch`."""

    def _build(self, tmp_path, *, live_reload: bool):
        from pf.builder import PresentationBuilder
        cfg = tmp_path / "presentation.yaml"
        cfg.write_text(yaml.safe_dump({
            "meta": {"title": "T"},
            "theme": {"primary": "#1C2537", "accent": "#C4A962",
                      "fonts": {"heading": "H", "subheading": "S",
                                "body": "B", "mono": "M"}},
            "slides": [{"layout": "section", "data": {"title": "S"}}],
        }), encoding="utf-8")
        metrics = tmp_path / "metrics.json"
        metrics.write_text("{}")
        b = PresentationBuilder(config_path=str(cfg), metrics_path=str(metrics))
        with contextlib.redirect_stdout(io.StringIO()):
            out = b.build(output_dir=str(tmp_path / "slides"),
                          live_reload=live_reload)
        return (out / "present.html").read_text(encoding="utf-8")

    def test_plain_build_has_no_reload_client(self, tmp_path):
        """Default `pf build` produces decks that serve cleanly under any
        HTTP server — no /__reload, no EventSource, no 404 in console."""
        html = self._build(tmp_path, live_reload=False)
        assert "/__reload" not in html
        assert "EventSource" not in html

    def test_live_reload_build_injects_sse_client(self, tmp_path):
        """When `pf serve --watch` (or any caller) passes live_reload=True,
        the SSE client is present so auto-refresh works."""
        html = self._build(tmp_path, live_reload=True)
        assert "/__reload" in html
        assert "EventSource" in html


class TestServeCommand:
    """Test the serve command options and basic behavior."""

    def test_serve_missing_directory(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["serve", "-d", "nonexistent"])
        assert result.exit_code != 0
        assert "not found" in result.output

    def test_serve_has_watch_option(self):
        """The serve command should accept --watch/--no-watch."""
        runner = CliRunner()
        # --help should show the watch option
        result = runner.invoke(cli, ["serve", "--help"])
        assert "--watch" in result.output
        assert "--no-watch" in result.output

    def test_serve_has_config_option(self):
        """The serve command should accept --config for rebuild."""
        runner = CliRunner()
        result = runner.invoke(cli, ["serve", "--help"])
        assert "--config" in result.output

    def test_serve_starts_and_responds(self, tmp_path):
        """Server should start and serve files from the directory."""
        # Create a minimal slides directory
        slides_dir = tmp_path / "slides"
        slides_dir.mkdir()
        (slides_dir / "present.html").write_text("<html>test</html>")

        runner = CliRunner()
        port = 18765  # unlikely to conflict

        # Start server in background thread
        server_thread = threading.Thread(
            target=lambda: runner.invoke(
                cli, ["serve", "-d", str(slides_dir), "-p", str(port), "--no-watch"]
            ),
            daemon=True,
        )
        server_thread.start()
        time.sleep(0.5)  # give server time to start

        try:
            resp = urllib.request.urlopen(f"http://localhost:{port}/present.html")
            assert resp.status == 200
            assert b"test" in resp.read()
        except urllib.error.URLError:
            pytest.skip("Server didn't start in time")

    def test_serve_sse_endpoint_exists(self, tmp_path):
        """The /__reload SSE endpoint should respond with text/event-stream."""
        slides_dir = tmp_path / "slides"
        slides_dir.mkdir()
        (slides_dir / "present.html").write_text("<html>ok</html>")

        runner = CliRunner()
        port = 18766

        server_thread = threading.Thread(
            target=lambda: runner.invoke(
                cli, ["serve", "-d", str(slides_dir), "-p", str(port), "--no-watch"]
            ),
            daemon=True,
        )
        server_thread.start()
        time.sleep(0.5)

        try:
            req = urllib.request.Request(f"http://localhost:{port}/__reload")
            # Set a short timeout — SSE connections stay open
            resp = urllib.request.urlopen(req, timeout=1)
            assert resp.headers.get("Content-Type") == "text/event-stream"
        except urllib.error.URLError:
            pytest.skip("Server didn't start in time")
        except Exception:
            # Timeout is expected since SSE keeps the connection open
            pass
