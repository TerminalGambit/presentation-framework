# Implementation Plan — PF v0.3 (Post-CD Response)

**Source spec:** [docs/SPEC.md](SPEC.md)
**Date:** 2026-04-20
**Owner:** Jack Massey
**Target ship:** v0.3.0
**Workflow:** consumed by `/autonomous-build`

---

## Summary

v0.3 lands three audit-driven phases on top of v0.2.1: (1) a four-preset **theme pack** that breaks the single-theme monotony and exposes a `theme.preset` key, plumbed through `pf init` and a new `list_themes` MCP tool; (2) **PPTX editable parity** for the six layouts currently rasterized (`code`, `toc`, `chart`, `map`, `mermaid`, `video`), with a unified dispatch table and a `pf pptx --strict` flag that fails on any image fallback; (3) a **MAF integration spike** behind a feature flag — a `video-maf` layout, a frozen contract doc, and a stub-binary integration test that proves the pipeline without depending on a real MAF install (MAF is still pre-alpha at plan-time, no tagged release). Ending state: `main` tagged `v0.3.0`, CHANGELOG + release note shipped, full suite green on Python 3.10–3.12, existing decks rebuild with no visual regressions under `theme.preset: default`.

Pre-work (v0.2.1 release, stray-file cleanup, STATE.md freeze) is **already complete on `main` as of `af3d31e`** — Phase 0 verifies that and the working tree, then opens v0.3 work.

---

## Ask-Human Triggers (global)

These conditions stop autonomous execution and surface to Jack regardless of which task is running:

- **AH-G1** Any breaking change to existing YAML keys (other than additions) or to MCP tool signatures. Spec §3 + §8 forbid this.
- **AH-G2** Any new runtime dependency beyond what `python-pptx` and `Plotly` already pull in. Spec §8.
- **AH-G3** Tagging `v0.3.0` — final cut requires Jack's explicit go-ahead even if all preceding tasks pass.
- **AH-G4** Any change to the MAF stdout/stderr JSON contract or cache-key formula after T3.1 is committed (the contract is meant to freeze in this milestone).
- **AH-G5** Any deletion of work in `.planning/` or `.worktrees/` — both are historical context, not stale state. Investigate before removing.
- **AH-G6** Adding a font that is not Google-Fonts-hosted or is not Open Font License / Apache 2.0 / SIL — license check required.
- **AH-G7** Pushing to `origin/main` or any force-push. Spec §8 + global git rules.

---

## Phase 0 — Pre-work verification (size: S)

### Goal
Confirm the v0.2.1 release work in the spec's §4 is fully landed, the working tree is clean enough to start v0.3, and the `main` branch is the correct base. No code changes — only verification + housekeeping.

### Kill criteria
- `v0.2.1` tag missing from `main`, or `main` doesn't contain `af70ad6` (CHANGELOG/release note) and `af3d31e` (STATE.md freeze).
- Stray pip files (`=0.0.9`, `=0.1.9`, `=0.23`) reappear at repo root.
- `pytest -q` red on `main` before any v0.3 commits.

### Tasks

- [x] **T0.1** — Verify v0.2.1 release artifacts on `main`
  - **Creates/modifies**: none
  - **Depends on**: none
  - **Description**: Confirm `git tag --list | grep -x v0.2.1` returns the tag, `git log --oneline v0.2..v0.2.1` includes the six presenter-view commits + PDF fix, `CHANGELOG.md` has a `[0.2.1] — 2026-04-20` block, and `docs/release-notes/presenter-view.md` exists. If any are missing, raise an ask-human event — do not attempt to redo the release.
  - **Verification**: `git tag --list v0.2.1`, `grep -q "## \[0.2.1\]" CHANGELOG.md`, `test -f docs/release-notes/presenter-view.md`. All three must succeed (exit 0).
  - **Ask human if**: any artifact missing.
  - **Effort**: S

- [x] **T0.2** — Verify stray-file cleanup
  - **Creates/modifies**: none
  - **Depends on**: none
  - **Description**: Confirm `=0.0.9`, `=0.1.9`, `=0.23` are no longer at the repo root.
  - **Verification**: `ls | grep -E '^=' || true` returns empty.
  - **Ask human if**: never.
  - **Effort**: S

- [x] **T0.3** — Stage docs/SPEC.md + docs/PLAN.md as the only intended additions
  - **Creates/modifies**: commits `docs/SPEC.md`, `docs/PLAN.md`
  - **Depends on**: T0.1, T0.2
  - **Description**: Stage and commit only `docs/SPEC.md` and `docs/PLAN.md`. Leave the other untracked items (`.planning/AUDIT-2026-04-20-vs-claude-design.md`, `demo/*`, `.superpowers/`, `docs/plans/2026-03-05-*.md`, `docs/release-notes/presenter-view.md`, `examples/slides/`, `slides/`, `.mcp.json`) for Jack to triage — they predate v0.3 and are out of scope.
  - **Verification**: `git status --porcelain | grep -E "^A " | wc -l` reports 2; `git log -1 --name-only` shows only `docs/SPEC.md` and `docs/PLAN.md`.
  - **Ask human if**: any of the listed untracked items now contain content that Phase 1 would overwrite (e.g., a partial `theme/presets/` already exists). If so, surface the path.
  - **Effort**: S

- [x] **T0.4** — Baseline test suite green
  - **Creates/modifies**: none
  - **Depends on**: T0.3
  - **Description**: Run the full suite once on `main` so every later phase has a known-green baseline. If anything is red on `main`, that's a Phase 0 finding, not Phase 1's problem.
  - **Verification**: `pytest -q` exits 0. Record the test count for delta tracking.
  - **Ask human if**: any test fails on a clean checkout of `main`.
  - **Effort**: S

---

## Phase 1 — Theme pack (size: S)

### Goal
Same YAML + different `theme.preset` value produces visibly distinct first renders across all 16 layouts, all four new presets pass the existing WCAG-AA contrast checker, and `pf init --theme <name>` scaffolds a project pre-wired to a preset. New MCP tool `list_themes()` enumerates available presets without changing any existing tool's signature.

### Kill criteria
- Any preset fails contrast on `examples/presentation.yaml` after T1.10 is in.
- A non-preset deck (one that omits `theme.preset` entirely) renders differently than it did before this phase — backwards-compatibility is a hard line.

### Tasks

- [x] **T1.1** — Add `theme.preset` schema key + precedence rule
  - **Creates/modifies**: `pf/schema.json`, `pf/builder.py` (new helper `_load_preset`, called from `generate_variables_css`)
  - **Depends on**: T0.4
  - **Description**: Add optional `preset` string to the `theme` object in `pf/schema.json` (no `enum` — discovered at load time so plugin themes work too). In `pf/builder.py:generate_variables_css`, before reading `theme.primary`/`theme.accent`/`theme.fonts`, deep-merge the preset's defaults under the user's overrides: scalar keys in user config win, dict keys merge recursively. Write the merge helper in builder.py — no new module. If `theme.preset` is set but unresolvable, raise a Click exception with the available preset list. Default behavior (no `preset` key) is unchanged.
  - **Verification**: `pytest tests/test_theme.py -k preset -v` passes new test cases — preset alone, preset + overrides, unknown preset (raises), no preset (unchanged).
  - **Ask human if**: a precedence ambiguity emerges that the spec's D3 default (user-overrides-preset, deep-merge dict-into-dict) doesn't cleanly resolve.
  - **Effort**: M

- [x] **T1.2** — Create `theme/presets/` with the `default` preset
  - **Creates/modifies**: `theme/presets/default.yaml` (new)
  - **Depends on**: T1.1
  - **Description**: Extract the current dark-navy + gold + Playfair/Montserrat/Lato + IBM Plex Mono token set from `theme/variables.css` lines 9–48 into `theme/presets/default.yaml`. Schema: `name`, `description`, `primary`, `accent`, `secondary_accent`, `fonts: {heading, subheading, body, mono}`, `style`. Loader in T1.1 reads from `theme/presets/<name>.yaml` first, then any plugin-registered themes. Existing decks that omit `theme.preset` still hit the same hard-coded fallback in `generate_variables_css` — they must not be re-routed through preset loading.
  - **Verification**: `python3 -m pf build -c examples/presentation.yaml -m examples/metrics.json -o /tmp/pf-default-test` produces output byte-identical to the same command run on the parent commit (excluding generated timestamps): `diff -r /tmp/pf-default-test /tmp/pf-default-baseline` returns no differences in HTML or CSS.
  - **Ask human if**: never.
  - **Effort**: S

- [x] **T1.3** — `editorial` preset (warm off-white + plum + serif)
  - **Creates/modifies**: `theme/presets/editorial.yaml`
  - **Depends on**: T1.2
  - **Description**: Magazine-style preset. Tokens: `primary: #FAF7F2` (warm off-white), `accent: #6B2737` (deep plum), `secondary_accent: #2A2A2A`, `fonts.heading: "Source Serif 4"`, `fonts.subheading: "Inter"`, `fonts.body: "Inter"`, `fonts.mono: "IBM Plex Mono"`, `style: minimal`. The light background triggers `_is_light` in builder.py:399 — verify `--pf-contrast-text` resolves to a dark color in the generated CSS. All fonts on Google Fonts (D1 default; license check satisfied by Google Fonts catalog — OFL).
  - **Verification**: `python3 -c "from pf.builder import PresentationBuilder; from pf.contrast import check_contrast; b = PresentationBuilder('examples/presentation.yaml','examples/metrics.json'); cfg = {'preset':'editorial'}; warnings = check_contrast('#FAF7F2','#6B2737','#2A2A2A'); assert warnings == [], warnings"` exits 0.
  - **Ask human if**: AH-G6 (font license uncertainty) — Source Serif 4 is OFL on Google Fonts, but verify before adding.
  - **Effort**: S

- [x] **T1.4** — `terminal` preset (near-black + phosphor green + JetBrains Mono)
  - **Creates/modifies**: `theme/presets/terminal.yaml`
  - **Depends on**: T1.2
  - **Description**: Tokens: `primary: #0D1117`, `accent: #4AF626` (phosphor green), `secondary_accent: #58A6FF`, `fonts.heading: "JetBrains Mono"`, `fonts.subheading: "JetBrains Mono"`, `fonts.body: "JetBrains Mono"`, `fonts.mono: "JetBrains Mono"`, `style: bold`. All four font slots use the same family — terminal aesthetic.
  - **Verification**: `check_contrast('#0D1117','#4AF626','#58A6FF') == []`; `pf build` with this preset on `examples/presentation.yaml` produces zero contrast warnings.
  - **Ask human if**: never.
  - **Effort**: S

- [x] **T1.5** — `plex` preset (CD-interop neutral + IBM Plex stack)
  - **Creates/modifies**: `theme/presets/plex.yaml`
  - **Depends on**: T1.2
  - **Description**: Mirrors Claude Design's default stack for stakeholder interop. Tokens: `primary: #F7F5F2`, `accent: #1F2937`, `secondary_accent: #6B5BA2`, `fonts.heading: "IBM Plex Sans"`, `fonts.subheading: "IBM Plex Sans"`, `fonts.body: "IBM Plex Sans"`, `fonts.mono: "IBM Plex Mono"`, `style: minimal`. (The spec mentions IBM Plex Serif for pull quotes — keep `heading` as Plex Sans for the header partial; quote layout can pick up Plex Serif via a future per-layout font override, but that's out of scope here.)
  - **Verification**: contrast clean; `pf build` on `examples/presentation.yaml` zero warnings; rendered HTML contains `IBM+Plex+Sans` in the Google Fonts CDN URL.
  - **Ask human if**: never.
  - **Effort**: S

- [x] **T1.6** — `nord` preset (cool slate + arctic blue)
  - **Creates/modifies**: `theme/presets/nord.yaml`
  - **Depends on**: T1.2
  - **Description**: Tokens: `primary: #2E3440`, `accent: #88C0D0` (arctic blue), `secondary_accent: #A3BE8C` (aurora green), `fonts.heading: "Inter"`, `fonts.subheading: "Inter"`, `fonts.body: "Inter"`, `fonts.mono: "JetBrains Mono"`, `style: modern`.
  - **Verification**: contrast clean; `pf build` on `examples/presentation.yaml` zero warnings.
  - **Ask human if**: never.
  - **Effort**: S

- [x] **T1.7** — `pf init --theme <name>` flag
  - **Creates/modifies**: `pf/cli.py:init`
  - **Depends on**: T1.2
  - **Description**: Add `--theme` Click option to the `init` command. When set, write `theme: {preset: <name>}` into the scaffold's `presentation.yaml` instead of the current hard-coded `primary`/`accent`/`fonts` block. Validate the preset exists (use the same loader from T1.1) and emit a Click exception with the available list on miss. When unset, scaffold defaults to `theme: {preset: default}` going forward — same visual output as today.
  - **Verification**: `pytest tests/test_cli.py -k 'init and theme' -v` passes new tests covering each of the five presets and one unknown name (raises). Manual: `python3 -m pf init /tmp/foo --theme nord && grep -q 'preset: nord' /tmp/foo/presentation.yaml`.
  - **Ask human if**: never.
  - **Effort**: S

- [x] **T1.8** — MCP `list_themes()` tool
  - **Creates/modifies**: `pf/mcp_server.py`
  - **Depends on**: T1.2
  - **Description**: Add a new `@mcp.tool()`-decorated function `list_themes()` returning `list[dict]` with shape `[{"name": str, "description": str, "screenshot_path": str}]`. `screenshot_path` is the relative path under the repo root (e.g., `docs/themes/nord.png`); D2 default is filesystem paths, not base64 (token cost). Plugin themes registered via entry points are included alongside built-in presets. Do not modify any existing tool's signature.
  - **Verification**: `pytest tests/test_mcp_server.py -k list_themes -v` passes a new test that asserts five entries (`default`, `editorial`, `terminal`, `plex`, `nord`), each with the three required keys. Existing MCP tests stay green.
  - **Ask human if**: AH-G1 if any change to `list_layouts` or other existing tool surfaces while wiring this in.
  - **Effort**: S

- [x] **T1.9** — Per-preset screenshots
  - **Creates/modifies**: `docs/themes/default.png`, `docs/themes/editorial.png`, `docs/themes/terminal.png`, `docs/themes/plex.png`, `docs/themes/nord.png`, `scripts/generate_theme_screenshots.py` (new)
  - **Depends on**: T1.3, T1.4, T1.5, T1.6
  - **Description**: One-off Python script that, for each preset, builds `examples/presentation.yaml` into a tmpdir with that preset overlaid, opens `slide_01.html` in Playwright at 1280×720, screenshots it, and writes to `docs/themes/<preset>.png`. The script is committed (so screenshots can be regenerated), the screenshots are committed (so `list_themes` returns paths to real files). Use the same Playwright shared-context pattern as `pf/pptx_native.py:export_pptx_editable`.
  - **Verification**: `python3 scripts/generate_theme_screenshots.py` exits 0 and produces all five PNGs at exactly 1280×720 (`python3 -c "from PIL import Image; assert Image.open('docs/themes/nord.png').size == (1280,720)"`).
  - **Ask human if**: never.
  - **Effort**: M

- [x] **T1.10** — Theme test suite
  - **Creates/modifies**: `tests/test_themes.py` (new)
  - **Depends on**: T1.1, T1.3, T1.4, T1.5, T1.6, T1.7, T1.8, T1.9
  - **Description**: One file that for each preset (parametrized) asserts: (a) the preset YAML loads, (b) all required CSS custom properties (`--pf-primary`, `--pf-accent`, `--pf-text`, `--pf-contrast-text`, `--pf-font-heading`, `--pf-font-subheading`, `--pf-font-body`, `--pf-font-mono`) appear in the generated CSS, (c) `check_contrast` returns no warnings on `examples/presentation.yaml`, (d) `screenshot_path` from `list_themes` exists on disk. Also one negative test: `pf build` with a non-existent preset raises with a helpful message listing available presets.
  - **Verification**: `pytest tests/test_themes.py -v` passes; coverage report shows the preset loader paths are exercised.
  - **Ask human if**: never.
  - **Effort**: M

### Phase 1 acceptance (matches spec §5.3)
1. `python3 -m pf build` with each preset on `examples/presentation.yaml` produces zero contrast warnings.
2. Visual diff (manual): same YAML + different preset = visibly distinct first render across the example deck.
3. `python3 -m pf init <name> --theme <preset>` works for all five presets.
4. `pytest tests/test_themes.py` green.

---

## Phase 2 — PPTX editable fidelity (size: M)

### Goal
`python3 -m pf pptx --editable examples/presentation.yaml` produces a deck where every slide has at least one editable text shape; `--strict` mode succeeds with zero image fallbacks. The 16-layout dispatch in `pf/pptx_native.py` is unified so adding a layout is a one-place edit.

### Kill criteria
- Any existing layout (the 10 already-native renderers) loses editability or changes visual output beyond a small (<5% pixel-diff) tolerance.
- `--strict` mode either silently succeeds when fallbacks happen, or fails with a misleading error.

### Tasks

- [x] **T2.1** — Unify dispatch + per-layout editable-shape coverage test (RED first)
  - **Creates/modifies**: `pf/pptx_native.py` (extract `LAYOUT_NAMES`, expose `iter_native_layouts()`), `tests/test_pptx_native.py` (new parametrized test)
  - **Depends on**: T0.4
  - **Description**: Pull the 16 layout names into a single `LAYOUT_NAMES = (...)` tuple at module top (sourced from `templates/layouts/*.html.j2` discovery, asserted at import time to match — drift breaks the build). Add a test that, for each layout, builds a one-slide fixture exercising that layout, exports `--editable`, opens the PPTX with `python-pptx`, and asserts the slide contains at least one shape that is not just an embedded picture (i.e., `shape.has_text_frame and shape.text_frame.text.strip()` is true on at least one shape, OR a chart/movie). Test starts RED for the six layouts not yet ported (`code`, `toc`, `chart`, `map`, `mermaid`, `video`) — that is the coverage gate driving T2.2–T2.7.
  - **Verification**: `pytest tests/test_pptx_native.py::test_each_layout_editable -v` shows 10/16 pass, 6/16 expected-fail (`pytest.xfail` initially); after T2.7 all 16 pass.
  - **Ask human if**: never.
  - **Effort**: M

- [x] **T2.2** — Editable `code` layout
  - **Creates/modifies**: `pf/pptx_native.py` (`_render_code` + `NATIVE_RENDERERS["code"]`)
  - **Depends on**: T2.1
  - **Description**: Render the `code` layout's source as a single text box in the theme's mono font (`theme["font_mono"]` — add it to `_pptx_theme()` if not present). Apply per-token color spans by walking the same Pygments / Highlight.js token output the HTML side uses — if Pygments isn't installed (it's optional), emit one uncolored run rather than failing. Background is theme primary; text wraps within slide bounds.
  - **Verification**: T2.1's coverage test passes for `code`; manual: opening the output in PowerPoint shows the code is selectable + editable as text (record one screenshot in `docs/plans/2026-04-20-pptx-editable-verification.md`).
  - **Ask human if**: AH-G2 — if syntax coloring requires adding Pygments as a hard dep. Default: keep it optional, fall back to uncolored.
  - **Effort**: M

- [x] **T2.3** — Editable `toc` layout with hyperlinks
  - **Creates/modifies**: `pf/pptx_native.py` (`_render_toc`)
  - **Depends on**: T2.1
  - **Description**: Numbered list of text boxes, one per TOC entry. Each entry's run gets a `click_action.target_slide = prs.slides[idx]` hyperlink. The TOC is generated by `pf/builder.py:_generate_toc` — re-derive it here from `config["slides"]` so PPTX output matches HTML.
  - **Verification**: T2.1 passes for `toc`; assert each text run on the TOC slide has `click_action.action == PP_ACTION.HYPERLINK_TO_SLIDE` (or equivalent — verify the python-pptx API for the constant). Manual: clicking a TOC entry in PowerPoint navigates to the right slide.
  - **Ask human if**: never.
  - **Effort**: M

- [x] **T2.4** — Editable `chart` layout via native pptx charts
  - **Creates/modifies**: `pf/pptx_native.py` (`_render_chart`)
  - **Depends on**: T2.1
  - **Description**: Map the YAML `chart.type` to `XL_CHART_TYPE` per D5: `bar→BAR_CLUSTERED`, `line→LINE`, `pie→PIE`, `donut→DOUGHNUT`, `scatter→XY_SCATTER`, `area→AREA`. Build `pptx.chart.data.CategoryChartData` (or `XyChartData` for scatter) from the YAML series, place via `slide.shapes.add_chart()`. Theme color: apply accent to the first series, secondary_accent to the second, then category accents. Plotly-only features (annotations, log axes, secondary y-axis, custom hover) emit a builder warning but the chart still renders with the supported subset. If chart type is unknown, fall back to image and (in `--strict`) fail.
  - **Verification**: T2.1 passes for `chart` (a chart shape counts as editable). Open in PowerPoint, double-click a chart — the data table opens and is editable.
  - **Ask human if**: a chart in `examples/presentation.yaml` uses a Plotly feature that loses meaningful information when downgraded.
  - **Effort**: L

- [x] **T2.5** — Editable annotations on `map` layout
  - **Creates/modifies**: `pf/pptx_native.py` (`_render_map`)
  - **Depends on**: T2.1
  - **Description**: Embed the rendered map image (current behavior — render once via Playwright into a static PNG, then `add_picture`), then on top, walk `data.markers[]` (or whatever the map layout's annotation list is in the schema) and add one editable text box per annotation positioned at the marker's projected (x,y). Marker x,y come from the map layout's data; if absolute pixel positions aren't available, position annotations along the slide's right edge as an editable legend.
  - **Verification**: T2.1 passes for `map` (annotations are editable text boxes). Manual: open in PowerPoint, edit a marker label.
  - **Ask human if**: the existing `map` layout's data shape doesn't carry per-marker position info — surface that gap before fabricating one.
  - **Effort**: M

- [x] **T2.6** — `mermaid` layout: image + source in slide notes
  - **Creates/modifies**: `pf/pptx_native.py` (`_render_mermaid`)
  - **Depends on**: T2.1
  - **Description**: Keep image rendering (Mermaid → SVG → PNG via existing path or Playwright capture), but populate the slide's `notes_text_frame` with the Mermaid source so a future tooling pass can regenerate the diagram from the deck. If the slide already has speaker notes, append the Mermaid source under a `--- mermaid source ---` separator rather than replacing.
  - **Verification**: T2.1 passes for `mermaid` (the notes text frame counts as editable text — confirm `slide.notes_slide.notes_text_frame.text` contains the Mermaid source on the assertion path). Manual: open in PowerPoint, view notes pane.
  - **Ask human if**: never.
  - **Effort**: S

- [x] **T2.7** — Editable `video` layout via `add_movie` + poster fallback
  - **Creates/modifies**: `pf/pptx_native.py` (`_render_video`)
  - **Depends on**: T2.1
  - **Description**: If `data.video` (or whatever the video layout's path key is — check `templates/layouts/video.html.j2`) points to a local file, embed via `slide.shapes.add_movie()` with the poster image as the preview. If the path is remote (`http://`/`https://`) or missing, render the poster image + a "Video: <caption>" editable text box + a clickable hyperlink to the URL.
  - **Verification**: T2.1 passes for `video`. Two test cases: local path (asserts a movie shape exists), remote path (asserts a poster picture + a text shape with the caption).
  - **Ask human if**: never.
  - **Effort**: M

- [x] **T2.8** — `pf pptx --strict` flag
  - **Creates/modifies**: `pf/cli.py:pptx`, `pf/pptx_native.py:export_pptx_editable` (collect fallback events, return them)
  - **Depends on**: T2.7
  - **Description**: Add `--strict` Click flag (only meaningful with `--editable`). `export_pptx_editable` returns a list of `(slide_index, layout, reason)` for any image fallback that occurred. CLI: in strict mode, if the list is non-empty, print each fallback reason and `raise SystemExit(1)` after the file is still written (so the user can inspect what fell back). Per D4, fallback in strict mode is a hard error (not a warning), implemented via exit code on the CLI.
  - **Verification**: `python3 -m pf pptx --editable --strict -c examples/presentation.yaml` exits 0 once T2.2–T2.7 are in. To verify the failure path: temporarily monkeypatch `NATIVE_RENDERERS` in a test to omit one renderer, assert `--strict` exits non-zero with the fallback summary in stderr.
  - **Ask human if**: never.
  - **Effort**: S

- [x] **T2.9** — QA verification artifact
  - **Creates/modifies**: `docs/plans/2026-04-20-pptx-editable-verification.md` (new)
  - **Depends on**: T2.8
  - **Description**: Markdown checklist documenting: built `examples/presentation.yaml` with `--editable --strict`, opened in PowerPoint (or Keynote), confirmed each of the 16 slides has editable primary text. Embed one screenshot per layout (kept inline as a relative `docs/plans/imgs/pptx-edit-<layout>.png`). This is the spec §6.4 manual-check artifact.
  - **Verification**: file exists; all 16 layouts present; one image per layout committed.
  - **Ask human if**: any layout fails the manual editability check despite T2.1's automated coverage passing.
  - **Effort**: S

### Phase 2 acceptance (matches spec §6.4)
1. `python3 -m pf pptx --editable examples/presentation.yaml` produces a deck where every slide has at least one editable text box.
2. `python3 -m pf pptx --editable --strict examples/presentation.yaml` succeeds with zero image fallbacks.
3. `tests/test_pptx_native.py::test_each_layout_editable` passes 16/16.
4. `docs/plans/2026-04-20-pptx-editable-verification.md` committed with one screenshot per layout.

---

## Phase 3 — MAF integration spike (size: L, ships as spike only)

### Goal
A new `video-maf` layout exists behind a `theme.experimental.maf_video: true` feature flag, the integration contract is frozen in `docs/maf-integration-contract.md`, and a stub-binary integration test proves the whole pipeline (compile → render → embed → cache → degrade gracefully) without depending on a real MAF install. With the flag off, builds are byte-identical to pre-Phase-3 output.

### Kill criteria
- Any code path involving `video-maf` runs when the flag is off.
- The contract doc is committed but contradicts what the spike implementation actually does.
- The spike requires Docker, network, or a real MAF install to pass tests.

### Tasks

- [x] **T3.1** — Freeze the integration contract
  - **Creates/modifies**: `docs/maf-integration-contract.md` (new)
  - **Depends on**: T0.4
  - **Description**: Single document covering: (a) `video-maf` layout's accepted YAML fields (`manifest_path`, `inline_spec`, `cache_key_strategy`, `caption_output`, `poster`); (b) PF→MAF subprocess call shape — `maf render <manifest> --quiet --json` (exact CLI string), expected stdout JSON shape (`{ "render_result": {...}, "artifacts": {"mp4": "...", "srt": "...", "vtt": "..."} }`), expected stderr taxonomy; (c) cache key formula `sha256(manifest_bytes + maf_version + env_digest)` and where each component comes from; (d) PPTX fallback contract (poster + hyperlink + caption text); (e) pinned target `MAF v0.1.0+`, with an explicit note that v0.3 spike runs only against the stub binary (D6 default — MAF still pre-alpha at plan-time per its own `docs/PLAN.md`); (f) explicit non-goals from spec §7.4.
  - **Verification**: file exists; cross-references the spec §7 sections it implements; reviewed by Jack (this is an AH-G3-adjacent gate — surface the doc for review before T3.2 starts).
  - **Ask human if**: Jack hasn't approved the contract before downstream tasks begin.
  - **Effort**: M

- [x] **T3.2** — Stub `maf` binary fixture
  - **Creates/modifies**: `tests/fixtures/video-maf-placeholder/maf` (executable shell script), `tests/fixtures/video-maf-placeholder/manifest.maf.yaml`, `tests/fixtures/video-maf-placeholder/expected/*.mp4`, `expected/*.srt`, `expected/*.vtt`, `expected/render_result.json`
  - **Depends on**: T3.1
  - **Description**: Shell script that mimics `maf render`: parses `--json` flag, reads the manifest path, copies pre-baked artifacts from `expected/` to a `--out`-specified directory (or default `./maf-out/`), and prints the documented JSON to stdout. Exits 0 on happy path, 2 on missing manifest. The pre-baked mp4 can be a 1-second silent black video (use `ffmpeg -f lavfi -i color=c=black:s=320x180:d=1 -c:v libx264 black.mp4` once, commit the result — single-digit KB).
  - **Verification**: `bash tests/fixtures/video-maf-placeholder/maf render tests/fixtures/video-maf-placeholder/manifest.maf.yaml --quiet --json --out /tmp/maf-stub-out` prints the documented JSON shape and writes mp4 + srt + vtt to `/tmp/maf-stub-out/`.
  - **Ask human if**: never.
  - **Effort**: M

- [x] **T3.3** — `video-maf` layout template
  - **Creates/modifies**: `templates/layouts/video-maf.html.j2` (new)
  - **Depends on**: T3.1
  - **Description**: Template renders a `<video>` element with `<source>` pointing at the slide-relative mp4 path the builder will populate, plus a `<track kind="captions" srclang="en" src="..." default>` for the vtt. Caption shown below per existing video layout pattern. Honors theme primary background.
  - **Verification**: render the template with a stub data dict using Jinja directly; output contains `<video>` and a `<track>` element.
  - **Ask human if**: never.
  - **Effort**: S

- [x] **T3.4** — Builder hook: subprocess + caching, behind feature flag
  - **Creates/modifies**: `pf/builder.py` (new method `_build_maf_video(slide_cfg)` invoked from `render_slide`), `pf/schema.json` (`theme.experimental.maf_video: bool`)
  - **Depends on**: T3.2, T3.3
  - **Description**: When `theme.experimental.maf_video` is true AND a slide's `layout == "video-maf"`, the builder: (a) computes the cache key per T3.1's formula, (b) checks `.pf-cache/maf/<key>/` — if present, reuses; (c) if absent and `maf` is on PATH, runs `subprocess.run(["maf", "render", manifest_path, "--quiet", "--json", "--out", cache_dir])` with a 5-minute timeout, (d) parses the JSON, copies the mp4/srt/vtt to the slide output dir, (e) hands the resolved paths to the template via `data`. When the flag is false, this code path is **not entered** — verified by an entry-point check at the top of the method that's tested with the flag both on and off.
  - **Verification**: `pytest tests/test_video_maf.py::test_flag_off_no_subprocess` mocks `subprocess.run` to fail and asserts no call happens with flag off; `test_flag_on_with_stub` puts the stub binary on PATH and asserts the slide renders with the embedded video.
  - **Ask human if**: AH-G2 — if subprocess invocation requires a new dep (it should not; `subprocess` is stdlib).
  - **Effort**: L

- [x] **T3.5** — Graceful degradation paths
  - **Creates/modifies**: `pf/builder.py` (extend T3.4's method)
  - **Depends on**: T3.4
  - **Description**: Three degradations: (1) flag on + `maf` not on PATH → emit a build warning (via `_warnings` list, same channel as overflow), render the layout's `poster` image as a static slide with the caption, exit 0. (2) flag on + `maf` on PATH but exits non-zero → emit warning with the exit code, render poster fallback, exit 0 (i.e., a broken MAF does not break the deck build — only `--strict` mode would). (3) flag on + manifest path missing → fail-fast (Click exception) since this is a spec error not an environment one.
  - **Verification**: `tests/test_video_maf.py` adds three cases mocking each degradation; in all three, the build still produces an output dir with `slide_NN.html` and the expected fallback content.
  - **Ask human if**: never.
  - **Effort**: M

- [x] **T3.6** — End-to-end integration test with stub binary
  - **Creates/modifies**: `tests/test_video_maf.py`
  - **Depends on**: T3.5
  - **Description**: One test that builds a one-slide presentation YAML with `theme.experimental.maf_video: true` and a `video-maf` slide pointing at the stub manifest, monkeypatches `PATH` to include `tests/fixtures/video-maf-placeholder/`, runs `PresentationBuilder().build()`, asserts the output mp4 + srt + vtt are present and the `<video>` tag in the slide HTML references them. Then runs build a second time and asserts cache hit (no subprocess call on the second run).
  - **Verification**: `pytest tests/test_video_maf.py -v` green.
  - **Ask human if**: never.
  - **Effort**: M

- [ ] **T3.7** — PPTX fallback for `video-maf`
  - **Creates/modifies**: `pf/pptx_native.py` (`_render_video_maf`), `LAYOUT_NAMES` extended to 17
  - **Depends on**: T3.4, T2.1
  - **Description**: PPTX render path uses the rendered mp4 (if present in cache) via `add_movie`, OR poster + hyperlink + caption if not. Per spec §7.4 explicit non-goal, no editability beyond the caption. Add `video-maf` to `LAYOUT_NAMES` so T2.1's coverage test runs against it (it should pass on the strength of the caption text box alone).
  - **Verification**: T2.1's parametrized test now runs 17 cases, all pass.
  - **Ask human if**: never.
  - **Effort**: S

### Phase 3 acceptance (matches spec §7.3)
1. With flag off: `pytest -q` shows zero behavioral change vs. before Phase 3 (existing tests + golden-output diff on `examples/`).
2. With flag on + stub `maf` on PATH: build embeds video + captions, second build hits cache.
3. With flag on + no `maf` on PATH: build warns, produces poster placeholder, exits 0.
4. `docs/maf-integration-contract.md` exists, reviewed by Jack (AH triggered in T3.1).

---

## Phase 4 — Release (size: S)

### Goal
v0.3.0 cut: docs updated, CHANGELOG + release note shipped, version bumped, suite green on Python 3.10/3.11/3.12, tag created, no force-push or premature push.

### Kill criteria
- Any of Phase 1/2/3 acceptance criteria red.
- Existing decks (`examples/`, `demo/`, `slides/`, `tsbc-moe-deck/`) show visual regressions under `theme.preset: default`.

### Tasks

- [ ] **T4.1** — Update README, SKILL, CLAUDE for new capabilities
  - **Creates/modifies**: `README.md`, `SKILL.md`, `CLAUDE.md`
  - **Depends on**: T1.10, T2.9, T3.6
  - **Description**: Add short sections to each: README — `--theme` flag + preset gallery (link to `docs/themes/`); SKILL.md — agent guidance for picking a preset, calling `list_themes`, using `--strict` PPTX, invoking the `video-maf` flag; CLAUDE.md — under "Common Mistakes" add: don't use `theme.preset` and `theme.primary` simultaneously without understanding D3 precedence; under "Tech Stack" mention the optional MAF subprocess.
  - **Verification**: `git diff README.md SKILL.md CLAUDE.md` shows additive sections; markdown still parses (`python3 -c "import markdown; markdown.markdown(open('README.md').read())"`).
  - **Ask human if**: never.
  - **Effort**: S

- [ ] **T4.2** — Release notes + CHANGELOG
  - **Creates/modifies**: `docs/release-notes/v0.3.0.md` (new), `CHANGELOG.md` (prepend `[0.3.0]` block)
  - **Depends on**: T4.1
  - **Description**: Release note covers: theme pack (4 new presets + `default` rename), `pf init --theme`, `list_themes` MCP tool, full PPTX editable parity + `--strict` flag, MAF integration spike (flag-gated, stub-tested, contract frozen). CHANGELOG entry summarizes Added/Changed/Fixed sections in the format established by `[0.2.1]`.
  - **Verification**: both files committed; CHANGELOG `[0.3.0]` section dated with the actual ship date (filled at tag time).
  - **Ask human if**: never.
  - **Effort**: S

- [ ] **T4.3** — Version bump + suite + tag (gated)
  - **Creates/modifies**: `setup.py` (version → `0.3.0`)
  - **Depends on**: T4.2
  - **Description**: Bump version, run `pytest -q` (must be green), run `tox` or equivalent across Python 3.10/3.11/3.12 if available locally, run `pf build` on `examples/`, `demo/`, `slides/`, `tsbc-moe-deck/` and visually confirm no regressions under `theme.preset: default`. Then **stop and ask** Jack to confirm the tag — do not run `git tag v0.3.0` autonomously.
  - **Verification**: pre-tag: `pytest -q` exit 0; rebuilds clean. Post-tag (after Jack approves): `git tag --list v0.3.0` returns the tag.
  - **Ask human if**: AH-G3 — final tag requires explicit approval. Also AH-G7 — do not push to origin without approval.
  - **Effort**: S

### Phase 4 acceptance (matches spec §9 milestone success)
1. `main` tagged `v0.3.0`.
2. `pf init --theme {editorial,terminal,plex,nord,default}` works end-to-end.
3. `pf pptx --editable --strict examples/presentation.yaml` succeeds.
4. `pf build` on `examples/presentation.yaml` with each preset produces zero contrast + zero overflow warnings.
5. `docs/maf-integration-contract.md` exists; `video-maf` spike test passes; flag defaults off.
6. Suite green on Python 3.10/3.11/3.12.
7. Existing decks rebuild with no visual regression under `theme.preset: default`.

---

## Appendix A: Open Questions (with defaults)

The spec listed six open decisions. Each is resolved here with a default the autonomous run will use unless Jack overrides.

- **D1 — Per-preset font stack.** Defaults baked into T1.3–T1.6 above. All fonts on Google Fonts (OFL or Apache 2.0): Source Serif 4, Inter, IBM Plex Sans/Mono/Serif, JetBrains Mono. Override before T1.3 if Jack wants different families.
- **D2 — `list_themes` returns paths or base64.** Default: filesystem paths (T1.8). Reason: token cost. Override only if MCP clients can't read repo files.
- **D3 — `theme.preset` vs user overrides precedence.** Default: deep-merge with user keys winning (T1.1). Scalars replace, dicts merge recursively. Documented in T4.1's CLAUDE.md update.
- **D4 — `--strict` failure mode.** Default: non-zero exit code at end of build, after the PPTX is still written so the user can inspect (T2.8). Reason: makes it scriptable in CI without throwing away artifacts.
- **D5 — Plotly → python-pptx chart-type mapping.** Default: bar/line/pie/donut/scatter/area cover the existing six. Plotly-only features (annotations, log axes, secondary y, custom hover) emit warnings but render the supported subset (T2.4). Unknown types fall back to image, which `--strict` then catches.
- **D6 — MAF spike target version.** Default: stub binary only (T3.2). Reason: MAF's own `docs/PLAN.md` shows Phase 0–1 still in flight and no tagged release as of 2026-04-20; gating the spike on a tag would push Phase 3 out of v0.3. Real-binary integration ships in v0.4 or later, against the contract frozen in T3.1.

---

## Appendix B: Effort + dependency summary

- Phase 0: 4 tasks (4S, 0M, 0L)
- Phase 1: 10 tasks (7S, 3M, 0L)
- Phase 2: 9 tasks (3S, 5M, 1L)
- Phase 3: 7 tasks (2S, 4M, 1L)
- Phase 4: 3 tasks (3S, 0M, 0L)

**Total: 33 tasks (19S, 12M, 2L). 7 ask-human triggers (1 global pre-baked, 6 task-scoped).**

Critical-path dependencies: T0.4 → T1.1 → T1.2 → {T1.3..T1.7, T1.8, T1.9} → T1.10 → T4.1; T0.4 → T2.1 → {T2.2..T2.7} → T2.8 → T2.9 → T4.1; T0.4 → T3.1 → {T3.2, T3.3} → T3.4 → T3.5 → T3.6 → T3.7 → T4.1.

Phases 1, 2, and 3 are independent post-T0.4 — the autonomous run can interleave them. Phase 4 fans in once all three are done.
