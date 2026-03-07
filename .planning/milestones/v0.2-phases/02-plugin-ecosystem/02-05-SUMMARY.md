---
phase: 02-plugin-ecosystem
plan: 05
subsystem: cli-plugins
tags:
  - cli
  - plugin-discovery
  - mcp
  - testing
dependency_graph:
  requires:
    - 02-01  # PluginRegistry (registry.py)
    - 02-02  # Builder integration (builder.py)
    - 02-03  # Theme system
    - 02-04  # Datasource resolution
  provides:
    - pf plugins CLI command group (list, install, info)
    - Updated MCP list_layouts with plugin source indicator
  affects:
    - pf/cli.py
    - pf/mcp_server.py
    - tests/test_cli.py
tech_stack:
  added:
    - Click testing (CliRunner) for CLI integration tests
    - unittest.mock.patch for subprocess isolation in tests
  patterns:
    - subprocess.run with sys.executable for correct-interpreter pip install
    - Best-effort registry discovery in MCP tools (exceptions caught, never block)
    - source field in MCP results to distinguish core vs plugin layouts
key_files:
  created:
    - tests/test_cli.py
  modified:
    - pf/cli.py
    - pf/mcp_server.py
decisions:
  - Use sys.executable for pip install to avoid "wrong pip" pitfall
  - Best-effort plugin discovery in MCP list_layouts — exceptions caught to avoid blocking the JSON-RPC channel
  - Plugin layouts appended after core layouts in list_layouts result with source field
metrics:
  duration: 2 min
  completed: "2026-03-06"
  tasks: 2
  files_modified: 3
  files_created: 1
---

# Phase 02 Plan 05: CLI Plugin Commands and MCP Update Summary

**One-liner:** `pf plugins` CLI command group (list/install/info) using PluginRegistry, plus MCP list_layouts updated to surface plugin layouts with source indicators.

## Objective

Add a `pf plugins` command group so users can discover installed plugins, install new ones from PyPI, and inspect plugin metadata. Update the MCP `list_layouts()` tool to return both core and plugin layouts.

## Tasks Completed

### Task 1 — Add pf plugins command group (list, install, info) to CLI
**Commit:** daf8b87

Added a `plugins` group with three subcommands to `pf/cli.py`:

- **`plugins list`**: Discovers via `PluginRegistry().discover()` and formats output in three labelled sections (Layouts, Themes, Data Sources). Each shows count and sorted names with descriptions. Empty sections show "(none installed)".
- **`plugins install <package>`**: Calls `subprocess.run([sys.executable, "-m", "pip", "install", package])`. Uses `sys.executable` to guarantee the correct Python interpreter is used regardless of PATH configuration. Prints green success or red failure message.
- **`plugins info <name>`**: Searches layouts, themes, then datasources in order. Displays type, version, description, and paths. Exits 1 with clear message if not found.

Imported `LayoutPlugin` and `PluginRegistry` at the top of `cli.py`.

### Task 2 — Update MCP list_layouts() and write CLI tests
**Commit:** 460077f

**MCP update (`pf/mcp_server.py`):**
- `list_layouts()` now returns core layouts with `"source": "core"` and plugin layouts with `"source": "plugin"`.
- Plugin discovery is wrapped in a broad `except Exception` so MCP tool failures from broken plugins never corrupt the JSON-RPC channel.
- Example result shape:
  ```python
  [
    {"name": "title", "source": "core", "description": "Opening slide..."},
    {"name": "kanban", "source": "plugin", "description": "Kanban board layout"},
  ]
  ```

**Tests (`tests/test_cli.py`)** — 5 tests, all passing:
1. `test_plugins_list` — exit 0, output has "Installed Plugins", "Layouts", "Themes", "Data Sources"
2. `test_plugins_install_calls_pip` — mocked `subprocess.run`, asserts called with `[sys.executable, "-m", "pip", "install", "pf-layout-test"]`
3. `test_plugins_install_failure` — mocked returncode=1, asserts non-zero exit and failure message
4. `test_plugins_info_not_found` — non-zero exit and "not found" in output for unknown plugin
5. `test_plugins_help` — exit 0 and "list", "install", "info" all present

## Verification Results

```
python3 -m pf plugins --help        # Shows list, install, info subcommands  PASS
python3 -m pf plugins list          # Shows 3 empty sections on clean install PASS
python3 -m pytest tests/test_cli.py # 5/5 passed                              PASS
python3 -m pytest tests/            # 308/308 passed                           PASS
```

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check: PASSED

- FOUND: tests/test_cli.py
- FOUND: pf/cli.py
- FOUND: pf/mcp_server.py
- FOUND: commit daf8b87 (Task 1)
- FOUND: commit 460077f (Task 2)
