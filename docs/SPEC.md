# Presentation Framework — v0.3 Specification

**Milestone name:** Post-CD Response
**Source brief:** [.planning/AUDIT-2026-04-20-vs-claude-design.md](../.planning/AUDIT-2026-04-20-vs-claude-design.md)
**Date:** 2026-04-20
**Owner:** Jack Massey
**Target ship:** v0.3.0
**Workflow:** superpowers (this SPEC → `/plan-from-spec` → `docs/PLAN.md` → `/autonomous-build`)

---

## 1. Why this milestone exists

Claude Design launched on 2026-04-17 as a prompt-driven visual generator. The audit concludes PF keeps its strategic lane (data-first, deterministic, agent-authorable) but must close CD's high-leverage polish gaps and widen its moat. v0.3 executes that stance in three focused phases.

The v0.3 "Visual Editor" milestone previously planned in `.planning/` is **deferred to v0.4**. The `.planning/` tree becomes historical; `docs/SPEC.md` + `docs/PLAN.md` are the live source of truth from here on.

---

## 2. Goal (one sentence)

Ship PF v0.3 with (a) a curated theme pack that breaks the single-theme monotony, (b) editable-PPTX parity across all 16 layouts, and (c) a de-risking spike of MAF video integration — without sacrificing determinism, WCAG compliance, or the MCP surface.

---

## 3. Out of scope

- Visual editor (Next.js/React canvas). Deferred to v0.4.
- Full MAF integration shipped end-to-end. MAF is pre-alpha; v0.3 ships a **spike + contract**, not a production `video-maf` layout.
- Content-intelligence / doc-to-deck drafting (CD already does this).
- 4:3 or custom aspect ratios.
- Any change to the default 1280×720 slide size.
- Breaking changes to existing YAML schema or `metrics.json` interpolation.

---

## 4. Pre-work — ship v0.2.1 first

Before v0.3 work begins, the in-flight presenter-view work lands as a point release so v0.3 starts from a clean base.

**P0.1** Merge `feature/presenter-view` → `main` as **v0.2.1**.
- Commits: `ea618d8`, `717defa`, `fca3c88`, `1d9a036`, `3975224`, `d39ae8f`.
- Tag `v0.2.1`, update `CHANGELOG.md` and `docs/release-notes/`.
- Write one release note covering presenter mode (P keybind, timer, audience hints, BroadcastChannel sync) + the PDF double-rotation fix.

**P0.2** Clean stray pip-misfire files at repo root: `=0.0.9`, `=0.1.9`, `=0.23`.

**P0.3** Freeze `.planning/STATE.md` with a final "superseded by docs/SPEC.md on 2026-04-20" note. Do not delete the directory — it's historical context.

Pre-work acceptance: `main` is tagged `v0.2.1`, CI green, working tree clean except `docs/SPEC.md` + `docs/PLAN.md`.

---

## 5. Phase 1 — Theme pack (size: S)

### 5.1 Intent
Close audit §5 item 1 (first-pass visual variety). Every current PF deck looks like the same dark-navy-gold deck. Ship **four curated themes** plus keep the current default, so first render variance matches CD's aesthetic-commitment phase.

### 5.2 Deliverables
- Four new built-in themes shipped as named presets under `theme/presets/`:
  1. **`editorial`** — warm off-white bg, deep plum accent, serif (Source Serif or similar), magazine-style.
  2. **`terminal`** — near-black bg, phosphor-green accent, JetBrains Mono everywhere, dense grid.
  3. **`plex`** — neutral light bg (#F7F5F2), IBM Plex Sans + Plex Mono + Plex Serif, mirrors CD's default stack explicitly for interop.
  4. **`nord`** — cool slate bg (#2E3440), arctic blue accent, Inter + JetBrains Mono, technical-report feel.
- Existing default theme renamed to **`default`** (dark #1C2537 + gold #C4A962) and exposed through the same preset mechanism.
- New top-level YAML key: `theme.preset: <name>` — loads the preset, then allows per-key overrides.
- Every preset passes WCAG AA at build time using the existing contrast checker (no new code).
- Every preset has a screenshot in `docs/themes/<name>.png` generated from a shared example deck.
- `pf init --theme <name>` scaffolds a new project with the chosen preset.
- MCP `list_layouts` companion: new MCP tool `list_themes()` returning `[{name, description, screenshot_path}]`.

### 5.3 Acceptance
- `pf build` with each preset produces zero contrast warnings on `examples/presentation.yaml`.
- Same YAML + different preset = visibly distinct first render across all 16 layouts.
- `pf init` accepts `--theme` flag and writes the correct preset name into the scaffold.
- Test: `tests/test_themes.py` loads each preset, asserts required CSS custom properties exist and contrast passes.

---

## 6. Phase 2 — PPTX editable fidelity (size: M)

### 6.1 Intent
Close audit §5 item 2. `pf/pptx_native.py` currently renders 10/16 layouts as editable text boxes; the remaining 6 fall back to image rasterization. Bring that to 16/16 so stakeholder-handoff decks are fully editable in PowerPoint/Keynote.

### 6.2 Layouts to add to `pf/pptx_native.py`
1. **`code`** — code as text box in a monospace font, not rasterized. Syntax coloring via per-token text runs; fall back to uncolored text if tokenization fails.
2. **`toc`** (table of contents) — numbered list of text boxes with hyperlinks to target slide indexes via python-pptx `click_action.target_slide`.
3. **`chart`** — native PowerPoint charts via `pptx.chart.data` for bar/line/pie/scatter/area/donut. Accept some visual drift from Plotly; editability is the goal.
4. **`map`** — render the map image (as today) but add editable annotation text boxes on top so labels/callouts are editable.
5. **`mermaid`** — render as image (keep image fallback) but include the Mermaid source in slide notes for round-trip regeneration.
6. **`video`** — embed the referenced video file with `add_movie`; fall back to poster image + caption if the video path is remote.

### 6.3 Shared improvements
- Unify the 16-layout dispatch table in `pptx_native.py` so adding a layout is one place, not scattered.
- `pf pptx` gains a `--strict` flag that fails instead of falling back to image for any layout.
- Coverage test: for each of the 16 layouts, `tests/test_pptx_native.py` asserts at least one editable shape exists on the output slide (no shape ⇒ fail).

### 6.4 Acceptance
- `pf pptx examples/presentation.yaml` produces a deck where every slide has at least one editable text box.
- `pf pptx --strict` succeeds on `examples/presentation.yaml` with zero image fallbacks.
- Manual check: opening the output in PowerPoint, every slide's primary text is editable (recorded in `docs/plans/2026-04-20-pptx-editable-verification.md` as a QA artifact).

---

## 7. Phase 3 — MAF integration spike (size: L, shipped as spike only)

### 7.1 Intent
Open audit §7 moat-widening. MAF is pre-alpha (its own `docs/PLAN.md` is still at Phase 0 scaffolding). v0.3 does **not** ship production MAF integration; it ships a **spike plus a frozen contract** so v0.4 or v0.5 can close it without rework.

### 7.2 Deliverables
- **New layout `video-maf`** behind a feature flag (`theme.experimental.maf_video: true`). Off by default.
- **Contract document** `docs/maf-integration-contract.md` defining:
  - The exact fields accepted by the `video-maf` layout (manifest path, inline spec, cache key strategy, caption output location).
  - PF → MAF invocation: shells out to `maf render` (subprocess), expects the documented MAF stdout/stderr JSON contract (`render_result.json`) and the `.mp4 + .srt + .vtt` artifact paths.
  - Cache key: `sha256(manifest + maf_version + env_digest)` matching MAF's deterministic key.
  - PPTX fallback: poster image + link to mp4 + "Video: <caption>" text.
  - Pinned MAF version target: **MAF v0.1.0 or later**. Spike tests against current HEAD only if MAF has at least Phase 0 + 1 done.
- **Spike implementation:**
  - Layout template `templates/layouts/video-maf.html.j2` rendering `<video>` + caption `<track>`.
  - Builder hook that, when flag is on and `maf` is on PATH, runs `maf render --quiet` and embeds the result.
  - Graceful degradation: if `maf` missing → build warning + poster placeholder, not a hard error.
- **Integration test:** one golden fixture `tests/fixtures/video-maf-placeholder/` using a stubbed `maf` binary (shell script that emits a known mp4 + srt). Confirms the whole pipeline without depending on a real MAF install.

### 7.3 Acceptance
- With flag off: zero behavioral change to existing builds.
- With flag on + stub `maf` on PATH: build produces a slide with embedded video + captions, cache hit on rebuild.
- With flag on + no `maf`: build warns, produces placeholder, exits 0.
- `docs/maf-integration-contract.md` exists and is reviewed by Jack before merge.

### 7.4 Explicit non-goals for the spike
- No Docker wrapping. MAF owns its Docker story.
- No live-reload support for MAF slides. A MAF slide forces a one-shot build.
- No PPTX editability for MAF slides beyond poster + link.

---

## 8. Non-functional requirements (apply to every phase)

- **Determinism preserved.** Same YAML + metrics.json + theme = byte-identical HTML output (excluding MAF slides, which inherit MAF's determinism story).
- **WCAG AA.** Every new theme passes the existing contrast checker. No regression in existing checks.
- **MCP surface stable.** No existing MCP tool's signature changes. New tools are additive (`list_themes`).
- **Test coverage.** Every new module has at least one unit or integration test. Overall line coverage ≥ current baseline.
- **No new runtime deps** beyond what python-pptx and Plotly already pull in. MAF is a subprocess, not an import.
- **Docs updated.** `README.md`, `SKILL.md`, and `CLAUDE.md` get short sections for each new capability.

---

## 9. Success criteria (milestone-level)

v0.3.0 ships when all of the following are true:

1. `main` is tagged `v0.3.0` with a full release note.
2. `pf init --theme editorial|terminal|plex|nord|default` all work end-to-end.
3. `pf pptx --strict examples/presentation.yaml` succeeds.
4. Running `pf build` on the existing `examples/presentation.yaml` with each preset produces zero contrast warnings and zero overflow warnings.
5. `docs/maf-integration-contract.md` exists; `video-maf` spike passes its integration test; flag defaults off.
6. Full test suite green on Python 3.10, 3.11, 3.12.
7. Existing decks (`examples/`, `demo/`, `slides/`) rebuild with no visual regressions under `theme.preset: default`.

---

## 10. Open decisions for `/plan-from-spec` to resolve

These are intentional gaps the plan step must close before execution:

- **D1** Exact font stack per preset (final font choices, fallback chain, license check).
- **D2** Whether `list_themes` MCP tool returns base64 screenshots or filesystem paths.
- **D3** How to handle `theme.preset: X` combined with user-level overrides when they conflict (precedence rule).
- **D4** Whether `pf pptx --strict` is an error on fallback or a warning promoted to error via exit code only.
- **D5** Exact chart-type mapping from Plotly config to python-pptx chart type (six types, some Plotly features won't translate).
- **D6** Whether MAF spike targets HEAD or waits for a tagged MAF release — gated by MAF's actual shipping cadence at plan-time.

---

## 11. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| MAF ships nothing tagged by plan-time | High | Medium | Spike targets stubbed binary; real integration waits for v0.4 |
| python-pptx chart API can't match Plotly variety | Medium | Medium | Accept visual drift; document per-chart-type caveats |
| Theme pack introduces contrast regressions on edge layouts | Medium | Low | CI runs contrast checker on all presets × all layouts |
| Presenter-view merge conflicts with v0.3 edits | Low | Low | Merge v0.2.1 first (P0.1), before any v0.3 work |
| Feature-flag for `video-maf` leaks into non-flag code paths | Low | High | Single entry-point check; tested with flag on AND off |

---

## 12. What this document is NOT

- Not a plan. No task list, no task IDs, no acceptance test fixtures. `/plan-from-spec` produces those.
- Not a roadmap. v0.4 (visual editor) and v0.5 (full MAF) are out of scope here.
- Not durable long-term docs. Archive to `docs/archive/` after v0.3 ships.

---

*End of SPEC. Next step: `/plan-from-spec` reads this file and writes `docs/PLAN.md` with phased tasks, dependencies, verification, and ask-human triggers.*
