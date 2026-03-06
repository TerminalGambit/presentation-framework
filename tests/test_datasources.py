"""Tests for datasource plugin resolution in PresentationBuilder."""

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import click
import pytest
import yaml

from pf.builder import PresentationBuilder
from pf.registry import DataSourcePlugin, PluginCredentialError, PluginRegistry


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

THEME_BASE = {
    "primary": "#1C2537",
    "accent": "#C4A962",
    "fonts": {
        "heading": "Playfair Display",
        "subheading": "Montserrat",
        "body": "Lato",
    },
}

MINIMAL_SLIDE = {"layout": "title", "data": {"title": "Test"}}


def _make_config(tmp_path: Path, datasources=None, slides=None):
    """Write a minimal presentation.yaml and return the path."""
    config = {
        "meta": {"title": "Test"},
        "theme": THEME_BASE,
        "slides": slides or [MINIMAL_SLIDE],
    }
    if datasources is not None:
        config["datasources"] = datasources

    config_path = tmp_path / "presentation.yaml"
    config_path.write_text(yaml.dump(config), encoding="utf-8")

    metrics_path = tmp_path / "metrics.json"
    metrics_path.write_text("{}", encoding="utf-8")
    return config_path, metrics_path


def _make_registry_with_ds(fetch_fn, name="mock_ds"):
    """Create a PluginRegistry pre-loaded with a single DataSourcePlugin."""
    registry = PluginRegistry()
    registry._datasources[name] = DataSourcePlugin(name=name, fetch_fn=fetch_fn)
    return registry


# ---------------------------------------------------------------------------
# 1. Fetch merges result into metrics; interpolation works end-to-end
# ---------------------------------------------------------------------------


class TestDatasourceFetchMergesMetrics:
    def test_datasource_fetch_merges_metrics(self, tmp_path):
        """Fetched data is merged into metrics so {{ metrics.external.revenue }} resolves."""

        def mock_fetch(config, creds):
            return {"revenue": 1000, "users": 50}

        registry = _make_registry_with_ds(mock_fetch, "mock_ds")

        datasources = [
            {"plugin": "mock_ds", "config": {"source": "test"}, "merge_key": "external"}
        ]
        slides = [
            {"layout": "title", "data": {"title": "{{ metrics.external.revenue }}"}}
        ]
        config_path, metrics_path = _make_config(tmp_path, datasources=datasources, slides=slides)

        builder = PresentationBuilder(
            str(config_path), str(metrics_path), registry=registry
        )
        out = builder.build(output_dir=str(tmp_path / "slides"))

        slide_html = (out / "slide_01.html").read_text(encoding="utf-8")
        assert "1000" in slide_html

    def test_fetch_fn_receives_config_and_credentials(self, tmp_path):
        """fetch_fn is called with the entry's config dict and the merged credentials."""
        received = {}

        def mock_fetch(config, creds):
            received["config"] = config
            received["creds"] = creds
            return {"ok": True}

        registry = _make_registry_with_ds(mock_fetch, "mock_ds")
        datasources = [{"plugin": "mock_ds", "config": {"sheet_id": "abc"}, "merge_key": "data"}]
        config_path, metrics_path = _make_config(tmp_path, datasources=datasources)

        builder = PresentationBuilder(str(config_path), str(metrics_path), registry=registry)
        builder.build(output_dir=str(tmp_path / "slides"))

        assert received["config"] == {"sheet_id": "abc"}
        assert isinstance(received["creds"], dict)


# ---------------------------------------------------------------------------
# 2. Missing credentials halt build with PluginCredentialError
# ---------------------------------------------------------------------------


class TestMissingCredentialsRaises:
    def test_missing_credentials_raises(self, tmp_path):
        """PluginCredentialError from fetch_fn raises click.ClickException and halts the build."""

        def mock_fetch(config, creds):
            raise PluginCredentialError("Missing API key")

        registry = _make_registry_with_ds(mock_fetch, "cred_ds")
        datasources = [{"plugin": "cred_ds"}]
        config_path, metrics_path = _make_config(tmp_path, datasources=datasources)

        builder = PresentationBuilder(str(config_path), str(metrics_path), registry=registry)

        with pytest.raises(click.ClickException) as exc_info:
            builder.build(output_dir=str(tmp_path / "slides"))

        assert "Missing API key" in str(exc_info.value.format_message())

    def test_credential_error_message_contains_plugin_name(self, tmp_path):
        """The ClickException message includes the datasource plugin name."""

        def mock_fetch(config, creds):
            raise PluginCredentialError("No token")

        registry = _make_registry_with_ds(mock_fetch, "sheets")
        datasources = [{"plugin": "sheets"}]
        config_path, metrics_path = _make_config(tmp_path, datasources=datasources)

        builder = PresentationBuilder(str(config_path), str(metrics_path), registry=registry)

        with pytest.raises(click.ClickException) as exc_info:
            builder.build(output_dir=str(tmp_path / "slides"))

        assert "sheets" in str(exc_info.value.format_message())


# ---------------------------------------------------------------------------
# 3. Unknown plugin warns and continues (build succeeds)
# ---------------------------------------------------------------------------


class TestDatasourcePluginNotFoundWarns:
    def test_datasource_plugin_not_found_warns(self, tmp_path, capsys):
        """Unknown datasource plugin emits a warning and build completes successfully."""
        registry = PluginRegistry()  # Empty registry — no plugins registered
        datasources = [{"plugin": "nonexistent"}]
        config_path, metrics_path = _make_config(tmp_path, datasources=datasources)

        builder = PresentationBuilder(str(config_path), str(metrics_path), registry=registry)
        out = builder.build(output_dir=str(tmp_path / "slides"))

        # Build completed without raising
        assert (out / "slide_01.html").exists()

    def test_datasource_plugin_not_found_output(self, tmp_path, capsys):
        """A warning message is printed when plugin is not found."""
        registry = PluginRegistry()
        datasources = [{"plugin": "nonexistent"}]
        config_path, metrics_path = _make_config(tmp_path, datasources=datasources)

        builder = PresentationBuilder(str(config_path), str(metrics_path), registry=registry)
        builder.build(output_dir=str(tmp_path / "slides"))

        captured = capsys.readouterr()
        combined = captured.out + captured.err
        assert "nonexistent" in combined


# ---------------------------------------------------------------------------
# 4. General fetch errors warn and continue (non-fatal)
# ---------------------------------------------------------------------------


class TestDatasourceFetchErrorWarnsContinues:
    def test_datasource_fetch_error_warns_continues(self, tmp_path):
        """RuntimeError from fetch_fn is non-fatal: build completes, metric not merged."""

        def failing_fetch(config, creds):
            raise RuntimeError("API timeout")

        registry = _make_registry_with_ds(failing_fetch, "failing_ds")
        datasources = [{"plugin": "failing_ds", "merge_key": "api_data"}]
        config_path, metrics_path = _make_config(tmp_path, datasources=datasources)

        builder = PresentationBuilder(str(config_path), str(metrics_path), registry=registry)
        out = builder.build(output_dir=str(tmp_path / "slides"))

        # Build completed
        assert (out / "slide_01.html").exists()
        # Metric was not merged (key absent from metrics)
        assert "api_data" not in builder.metrics

    def test_datasource_fetch_error_emits_warning(self, tmp_path, capsys):
        """A warning is printed when fetch_fn raises a general exception."""

        def failing_fetch(config, creds):
            raise ConnectionError("timeout")

        registry = _make_registry_with_ds(failing_fetch, "ds_timeout")
        datasources = [{"plugin": "ds_timeout"}]
        config_path, metrics_path = _make_config(tmp_path, datasources=datasources)

        builder = PresentationBuilder(str(config_path), str(metrics_path), registry=registry)
        builder.build(output_dir=str(tmp_path / "slides"))

        captured = capsys.readouterr()
        combined = captured.out + captured.err
        assert "ds_timeout" in combined


# ---------------------------------------------------------------------------
# 5. No datasources key — normal build (backward compatibility)
# ---------------------------------------------------------------------------


class TestNoDatasourcesKeyNormalBuild:
    def test_no_datasources_key_normal_build(self, tmp_path):
        """Presentation without datasources key builds identically to before."""
        config_path, metrics_path = _make_config(tmp_path)  # No datasources

        builder = PresentationBuilder(str(config_path), str(metrics_path))
        out = builder.build(output_dir=str(tmp_path / "slides"))

        assert (out / "slide_01.html").exists()
        assert (out / "present.html").exists()

    def test_no_datasources_metrics_unchanged(self, tmp_path):
        """Metrics dict is not modified when no datasources are declared."""
        metrics_data = {"summary": {"total": 42}}
        config_path = tmp_path / "presentation.yaml"
        config = {
            "meta": {"title": "Test"},
            "theme": THEME_BASE,
            "slides": [MINIMAL_SLIDE],
        }
        config_path.write_text(yaml.dump(config), encoding="utf-8")
        metrics_path = tmp_path / "metrics.json"
        metrics_path.write_text(json.dumps(metrics_data), encoding="utf-8")

        builder = PresentationBuilder(str(config_path), str(metrics_path))
        builder.build(output_dir=str(tmp_path / "slides"))

        assert builder.metrics.get("summary", {}).get("total") == 42


# ---------------------------------------------------------------------------
# 6. Credentials from environment variables
# ---------------------------------------------------------------------------


class TestCredentialsFromEnv:
    def test_credentials_from_env(self, tmp_path, monkeypatch):
        """PF_ env vars are passed as credentials to fetch_fn (lowercased key)."""
        monkeypatch.setenv("PF_TEST_KEY", "secret123")

        received_creds = {}

        def mock_fetch(config, creds):
            received_creds.update(creds)
            assert creds.get("pf_test_key") == "secret123", (
                f"Expected pf_test_key='secret123' in creds, got: {creds}"
            )
            return {"status": "ok"}

        registry = _make_registry_with_ds(mock_fetch, "env_ds")
        datasources = [{"plugin": "env_ds", "merge_key": "env_result"}]
        config_path, metrics_path = _make_config(tmp_path, datasources=datasources)

        builder = PresentationBuilder(str(config_path), str(metrics_path), registry=registry)
        builder.build(output_dir=str(tmp_path / "slides"))

        assert builder.metrics.get("env_result") == {"status": "ok"}
        assert received_creds.get("pf_test_key") == "secret123"

    def test_env_credentials_override_file_credentials(self, tmp_path, monkeypatch):
        """Env vars take precedence over .pf/credentials.json values."""
        # Create credentials file with a value
        pf_dir = tmp_path / ".pf"
        pf_dir.mkdir()
        (pf_dir / "credentials.json").write_text(
            json.dumps({"pf_api_key": "file_value"}), encoding="utf-8"
        )

        # Set env var to override
        monkeypatch.setenv("PF_API_KEY", "env_value")

        received_creds = {}

        def mock_fetch(config, creds):
            received_creds.update(creds)
            return {"done": True}

        registry = _make_registry_with_ds(mock_fetch, "override_ds")
        datasources = [{"plugin": "override_ds"}]
        config_path, metrics_path = _make_config(tmp_path, datasources=datasources)

        builder = PresentationBuilder(str(config_path), str(metrics_path), registry=registry)
        builder.build(output_dir=str(tmp_path / "slides"))

        # Env var overrides file credential
        assert received_creds.get("pf_api_key") == "env_value"


# ---------------------------------------------------------------------------
# 7. Credentials from .pf/credentials.json file
# ---------------------------------------------------------------------------


class TestCredentialsFromFile:
    def test_credentials_from_file(self, tmp_path):
        """Credentials in .pf/credentials.json are loaded and passed to fetch_fn."""
        pf_dir = tmp_path / ".pf"
        pf_dir.mkdir()
        (pf_dir / "credentials.json").write_text(
            json.dumps({"api_key": "file_secret"}), encoding="utf-8"
        )

        received_creds = {}

        def mock_fetch(config, creds):
            received_creds.update(creds)
            assert creds.get("api_key") == "file_secret", (
                f"Expected api_key='file_secret' in creds, got: {creds}"
            )
            return {"data": "loaded"}

        registry = _make_registry_with_ds(mock_fetch, "file_cred_ds")
        datasources = [{"plugin": "file_cred_ds", "merge_key": "file_result"}]
        config_path, metrics_path = _make_config(tmp_path, datasources=datasources)

        builder = PresentationBuilder(str(config_path), str(metrics_path), registry=registry)
        builder.build(output_dir=str(tmp_path / "slides"))

        assert builder.metrics.get("file_result") == {"data": "loaded"}
        assert received_creds.get("api_key") == "file_secret"

    def test_missing_credentials_file_is_safe(self, tmp_path):
        """If .pf/credentials.json does not exist, no error is raised."""
        received_creds = {}

        def mock_fetch(config, creds):
            received_creds.update(creds)
            return {"ok": True}

        registry = _make_registry_with_ds(mock_fetch, "safe_ds")
        datasources = [{"plugin": "safe_ds"}]
        config_path, metrics_path = _make_config(tmp_path, datasources=datasources)

        builder = PresentationBuilder(str(config_path), str(metrics_path), registry=registry)
        out = builder.build(output_dir=str(tmp_path / "slides"))

        assert (out / "slide_01.html").exists()
        # Credentials dict is empty (or may contain PF_* env vars from test environment)
        # The key point is no crash occurred
