# Changelog

All notable changes to presentation-framework are documented here. This project follows semantic versioning.

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
