"""
PluginRegistry — discovers layout, theme, and data-source plugins via Python
entry points (pip-installed packages) and local project directories.

Entry point groups:
  pf.layouts      — LayoutPlugin instances
  pf.themes       — ThemePlugin instances
  pf.datasources  — callable fetch(config, credentials) -> dict

Local discovery (no pip install required):
  <project_dir>/layouts/*.html.j2  → LocalLayoutPlugin (one per file)
  <project_dir>/themes/*.css       → local ThemePlugin stubs

The registry supplies ``get_template_loader(core_templates_dir)`` which builds
a ``jinja2.ChoiceLoader`` that checks plugin template directories first, then
falls back to the built-in core templates.  This keeps the builder entirely
backward compatible — adding the registry is additive-only.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from importlib.metadata import entry_points
from pathlib import Path
from typing import Callable

from jinja2 import ChoiceLoader, FileSystemLoader


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------


class PluginCredentialError(Exception):
    """Raised by a DataSourcePlugin when required credentials are missing."""


# ---------------------------------------------------------------------------
# Plugin dataclasses
# ---------------------------------------------------------------------------


@dataclass
class LayoutPlugin:
    """Contract for a pip-installable layout plugin.

    The plugin package must expose a ``pf.layouts`` entry point that returns an
    instance of this class (or a subclass).
    """

    name: str
    description: str = ""
    templates_dir: Path | None = None
    css_files: list[Path] = field(default_factory=list)
    version: str = "0.0.0"


@dataclass
class LocalLayoutPlugin:
    """Auto-created for each ``*.html.j2`` file found in ``<project>/layouts/``."""

    name: str
    template_path: Path


@dataclass
class ThemePlugin:
    """Contract for a pip-installable theme plugin.

    The plugin package must expose a ``pf.themes`` entry point that returns an
    instance of this class.
    """

    name: str
    description: str = ""
    defaults: dict = field(default_factory=dict)
    css_file: Path | None = None
    version: str = "0.0.0"


@dataclass
class DataSourcePlugin:
    """Wraps a ``fetch(config, credentials) -> dict`` callable.

    Raises ``PluginCredentialError`` when required credentials are absent.
    """

    name: str
    description: str = ""
    fetch_fn: Callable | None = None
    version: str = "0.0.0"


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


class PluginRegistry:
    """Discovers and holds all installed and local plugins.

    Usage::

        registry = PluginRegistry()
        registry.discover(project_dir=Path("."))
        loader = registry.get_template_loader(TEMPLATES_DIR)
    """

    def __init__(self) -> None:
        self._layouts: dict[str, LayoutPlugin | LocalLayoutPlugin] = {}
        self._themes: dict[str, ThemePlugin] = {}
        self._datasources: dict[str, DataSourcePlugin] = {}

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def discover(self, project_dir: Path | None = None) -> None:
        """Run all discovery routines.  Safe to call multiple times (idempotent
        for the same project_dir — subsequent calls *extend* the registry)."""
        self._discover_layouts(project_dir)
        self._discover_themes(project_dir)
        self._discover_datasources()

    def _discover_layouts(self, project_dir: Path | None) -> None:
        """Populate ``_layouts`` from entry points and local directory."""
        # 1. Entry-point plugins (pip-installed)
        eps = entry_points(group="pf.layouts")
        for ep in eps:
            try:
                plugin = ep.load()
                if not isinstance(plugin, LayoutPlugin):
                    warnings.warn(
                        f"pf.layouts entry point '{ep.name}' did not return a "
                        f"LayoutPlugin instance (got {type(plugin).__name__!r}). "
                        "Skipping.",
                        stacklevel=2,
                    )
                    continue
                self._layouts[plugin.name] = plugin
            except Exception as exc:  # noqa: BLE001
                warnings.warn(
                    f"Failed to load pf.layouts entry point '{ep.name}': {exc}. "
                    "Skipping.",
                    stacklevel=2,
                )

        # 2. Local directory scan
        if project_dir is not None:
            layouts_dir = project_dir / "layouts"
            if layouts_dir.is_dir():
                for template_path in sorted(layouts_dir.glob("*.html.j2")):
                    # kanban.html.j2  →  name = "kanban"
                    name = template_path.stem  # removes ".j2"
                    if name.endswith(".html"):
                        name = name[:-5]         # removes ".html"
                    if name in self._layouts:
                        warnings.warn(
                            f"Local layout '{name}' ({template_path}) shadows an "
                            "entry-point layout plugin with the same name.",
                            stacklevel=2,
                        )
                    self._layouts[name] = LocalLayoutPlugin(
                        name=name, template_path=template_path
                    )

    def _discover_themes(self, project_dir: Path | None) -> None:
        """Populate ``_themes`` from entry points and local directory."""
        eps = entry_points(group="pf.themes")
        for ep in eps:
            try:
                plugin = ep.load()
                if not isinstance(plugin, ThemePlugin):
                    warnings.warn(
                        f"pf.themes entry point '{ep.name}' did not return a "
                        f"ThemePlugin instance. Skipping.",
                        stacklevel=2,
                    )
                    continue
                self._themes[plugin.name] = plugin
            except Exception as exc:  # noqa: BLE001
                warnings.warn(
                    f"Failed to load pf.themes entry point '{ep.name}': {exc}. "
                    "Skipping.",
                    stacklevel=2,
                )

        # Local CSS theme files
        if project_dir is not None:
            themes_dir = project_dir / "themes"
            if themes_dir.is_dir():
                for css_path in sorted(themes_dir.glob("*.css")):
                    name = css_path.stem
                    self._themes[name] = ThemePlugin(
                        name=name, css_file=css_path
                    )

    def _discover_datasources(self) -> None:
        """Populate ``_datasources`` from entry points."""
        eps = entry_points(group="pf.datasources")
        for ep in eps:
            try:
                fetch_fn = ep.load()
                if not callable(fetch_fn):
                    warnings.warn(
                        f"pf.datasources entry point '{ep.name}' did not return "
                        "a callable. Skipping.",
                        stacklevel=2,
                    )
                    continue
                self._datasources[ep.name] = DataSourcePlugin(
                    name=ep.name, fetch_fn=fetch_fn
                )
            except Exception as exc:  # noqa: BLE001
                warnings.warn(
                    f"Failed to load pf.datasources entry point '{ep.name}': "
                    f"{exc}. Skipping.",
                    stacklevel=2,
                )

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def layout_names(self) -> list[str]:
        """Sorted list of all discovered layout names."""
        return sorted(self._layouts)

    @property
    def theme_names(self) -> list[str]:
        """Sorted list of all discovered theme names."""
        return sorted(self._themes)

    @property
    def datasource_names(self) -> list[str]:
        """Sorted list of all discovered data source names."""
        return sorted(self._datasources)

    # ------------------------------------------------------------------
    # Getters
    # ------------------------------------------------------------------

    def get_layout(self, name: str) -> LayoutPlugin | LocalLayoutPlugin | None:
        return self._layouts.get(name)

    def get_theme(self, name: str) -> ThemePlugin | None:
        return self._themes.get(name)

    def get_datasource(self, name: str) -> DataSourcePlugin | None:
        return self._datasources.get(name)

    # ------------------------------------------------------------------
    # Template loader
    # ------------------------------------------------------------------

    def get_template_loader(self, core_templates_dir: Path) -> ChoiceLoader:
        """Build a ``ChoiceLoader`` that resolves plugin templates before core.

        Search order:
          1. Each pip-installed LayoutPlugin's ``templates_dir`` (if set)
          2. Each LocalLayoutPlugin's parent directory
          3. Core ``templates/`` directory (always last — built-in fallback)
        """
        loaders: list[FileSystemLoader] = []

        for plugin in self._layouts.values():
            if isinstance(plugin, LayoutPlugin) and plugin.templates_dir is not None:
                loaders.append(FileSystemLoader(str(plugin.templates_dir)))
            elif isinstance(plugin, LocalLayoutPlugin):
                # The template lives in e.g. <project>/layouts/kanban.html.j2
                # Jinja2 looks for "layouts/<name>.html.j2" relative to the
                # loader root.  We need the *parent* of the layouts/ dir so
                # that "layouts/kanban.html.j2" resolves correctly.
                loaders.append(
                    FileSystemLoader(str(plugin.template_path.parent.parent))
                )

        # Core templates always last (fallback)
        loaders.append(FileSystemLoader(str(core_templates_dir)))

        return ChoiceLoader(loaders)
