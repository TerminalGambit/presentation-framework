# Changelog

All notable changes to presentation-framework are documented here. This project follows semantic versioning.

## [0.3.0] — 2026-04-20

Post-CD-audit milestone: a curated theme pack, editable-PPTX parity
across every built-in layout, and a feature-flagged MAF integration
spike. No breaking YAML or MCP changes.

### Added
- **Theme pack** — four new presets (`editorial`, `terminal`, `plex`,
  `nord`) plus a `default` preset that reproduces the pre-v0.3 dark
  navy + gold tokens byte-for-byte. Select with `theme.preset: <name>`.
  Each preset ships a 1280×720 preview PNG under `docs/themes/`.
- **`pf init --theme <preset>`** — scaffolds a deck pre-wired to a
  preset (defaults to `preset: default` when `--theme` is omitted).
- **MCP `list_themes()` tool** — returns `[{name, description,
  screenshot_path}]` for every built-in and plugin-registered preset.
- **Editable PPTX for the remaining 6 layouts** — `code` (syntax-
  colored mono text via optional Pygments), `toc` (NAMED_SLIDE
  hyperlinks per entry), `chart` (native python-pptx chart, double-
  clickable data table), `map` (raster + right-edge editable marker
  legend), `mermaid` (raster + diagram source in speaker notes),
  `video` (add_movie for local mp4, hyperlinked poster for remote
  URLs). All 16 built-in layouts now produce at least one editable
  shape under `pf pptx --editable`.
- **`pf pptx --strict`** — fail CI (exit 1) when any slide falls back
  to a rasterized image. File still written for inspection. Prints
  per-fallback slide/layout/reason to stderr.
- **MAF integration spike (experimental, flag-gated)** — new
  `video-maf` layout behind `theme.experimental.maf_video: true`.
  When on and the `maf` binary is on PATH, the builder shells out to
  `maf render` and embeds the resulting mp4 + vtt into the slide.
  Off / missing binary degrades to a poster still with a build
  warning. Cached renders keyed by sha256(manifest + maf_version +
  env_digest) under `.pf-cache/maf/`. Full contract in
  [`docs/maf-integration-contract.md`](docs/maf-integration-contract.md).

### Changed
- `_pptx_theme` now exposes `font_mono` (from `theme.fonts.mono`,
  default IBM Plex Mono) and `secondary_accent` so editable
  renderers can reach the same design tokens as the HTML side.
- `export_pptx_editable` now returns `list[dict]` of fallback events
  instead of `None` — callers that ignore the return value are
  unaffected; `--strict` consumes the list.
- `pf/pptx_native.py:LAYOUT_NAMES` grew to 17 (added `video-maf`).
  An import-time drift guard asserts the tuple matches
  `templates/layouts/*.html.j2` exactly.

### Fixed
- Light-theme typography vars (`--pf-font-heading` etc.) were only
  emitted by the dark-branch of `generate_variables_css` — surfaced
  by the theme pack's parametrized tests and refactored so both
  branches share the typography block.

### Notes
- No breaking changes to YAML keys or existing MCP tool signatures.
- Pygments is an optional dependency: install for per-token syntax
  coloring in PPTX `code` layouts; uncolored runs otherwise.
- Existing decks that omit `theme.preset` keep hitting the original
  hard-coded fallback in `generate_variables_css` — verified by a
  byte-identical render of `examples/presentation.yaml` pre- and
  post-v0.3 under `theme.preset: default`.

## [0.2.1] — 2026-04-20

Feature-level improvements accumulated on `main` since the `v0.2` tag. This release consolidates them under a single tag before the v0.3 milestone opens.

### Added
- **Presenter mode** — split-view layout showing current slide + next slide + speaker notes + elapsed/countdown timers. Toggle with `P`. Syncs across windows via `BroadcastChannel` so a second monitor stays in lockstep with the audience view.
- **Audience-hint visibility toggle** — `P` keybind hides/shows notes without leaving presenter mode.
- **Animation system** — five progressive-enhancement entry animations (fade, slide, scale, stagger, highlight pulse) wired through theme config; all degrade gracefully with `prefers-reduced-motion`.
- **Theme contrast variable** — new `--pf-contrast-text` CSS custom property emitted at build time for correct text color on light-background presets.

### Fixed
- **PDF export double-rotation** — portrait/landscape transform no longer compounded when Playwright re-measured the page.
- **Fragment control via postMessage** — reveal/hide now uses `postMessage` instead of shared state, with `↓`/`↑` as the keybinds.
- **Async test-cleanup flakiness** — `test_disconnect_cleanup` had a race around the dev-server SSE disconnect; added a timing guard.
- **Animations demo YAML shape** — the highlight-pulse slide used a nested `columns` array; corrected to explicit `left`/`right` keys.

### Polished
- Speaker-note panels render with `white-space: pre-line` so multi-line notes keep their line breaks.
- Presenter layout uses `50% / 1fr / auto` rows with `min-height: 0` so long notes scroll cleanly instead of capping.

### Notes
- No breaking YAML or MCP changes.
- Next milestone is **v0.3 — Post-CD Response** (theme pack, PPTX editable fidelity, MAF integration spike). See `docs/SPEC.md`.

## [0.2.0] — 2026-03-07

Initial release of the v0.2 overhaul: adaptive sizing, 4 new layouts, speaker notes, transitions, KaTeX math, PDF export, and expanded MCP surface. See `.planning/` history for the full phase record.
