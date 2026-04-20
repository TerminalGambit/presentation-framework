# PPTX editable-export verification — v0.3.0

**Spec reference:** §6.4 (Phase 2 — PPTX editable parity)
**Plan task:** T2.9
**Date:** 2026-04-20

## Purpose

Documents the evidence that every built-in layout in `pf/pptx_native.py`
produces at least one **editable** element (text box, native chart, movie
shape, or editable speaker notes) under `pf pptx --editable`, and that
`pf pptx --editable --strict examples/presentation.yaml` completes with
zero image-fallback events.

This file is the spec §6.4 verification artifact. It combines:

1. **Automated evidence** — captured programmatically from a one-slide
   export per layout; reproducible by re-running the fixtures below.
2. **End-to-end smoke** — `pf pptx --editable --strict` on
   `examples/presentation.yaml`, exit 0, 9 slides, 83 editable text
   shapes across the deck, zero fallbacks.
3. **Manual checklist** — blank checkboxes for Jack to tick after
   opening the export in PowerPoint or Keynote. Screenshots per layout
   are deferred until that manual pass (capturing them requires an
   interactive PowerPoint session, which this autonomous run can't
   drive). Once captured, drop the PNGs into
   `docs/plans/imgs/pptx-edit-<layout>.png` and update this doc.

## Acceptance gate summary

| Spec §6.4 criterion                                                           | Status    | Evidence                                         |
| ----------------------------------------------------------------------------- | --------- | ------------------------------------------------ |
| Every slide has ≥1 editable text box                                          | ✅         | 16/16 layouts, automated (see table below)       |
| `--editable --strict` on examples/ succeeds                                   | ✅         | Exit 0, 0 fallbacks                              |
| `tests/test_pptx_native.py::test_each_layout_editable` passes 16/16           | ✅         | 16 passed, 0 xfailed (post-T2.7)                 |
| Per-layout screenshot committed                                               | ⬜ pending | Manual PowerPoint pass — see checklist           |

## Automated per-layout inventory

One-slide fixture per layout, exported with `--editable`, inspected via
`python-pptx`. Columns:

- **Text**  — shape count with non-empty `text_frame.text`
- **Chart** — native `add_chart()` shapes
- **Media** — `add_movie()` / MSO_SHAPE_TYPE.MEDIA
- **Pic**   — pictures (map rasterizations, mermaid diagrams, video posters)
- **HL**    — shapes with a `click_action.action ∈ {HYPERLINK, NAMED_SLIDE}`
- **Notes** — chars written to `slide.notes_slide.notes_text_frame`

| Layout         | Text | Chart | Media | Pic | HL | Notes |
| -------------- | ---: | ----: | ----: | --: | -: | ----: |
| chart          |    1 |     1 |     0 |   0 |  0 |     0 |
| closing        |    2 |     0 |     0 |   0 |  0 |     0 |
| code           |    2 |     0 |     0 |   0 |  0 |     0 |
| data-table     |    6 |     0 |     0 |   0 |  0 |     0 |
| image          |    2 |     0 |     0 |   0 |  0 |     0 |
| map            |    3 |     0 |     0 |   1 |  0 |     0 |
| mermaid        |    1 |     0 |     0 |   1 |  0 |    39 |
| quote          |    2 |     0 |     0 |   0 |  0 |     0 |
| section        |    3 |     0 |     0 |   0 |  0 |     0 |
| stat-grid      |    3 |     0 |     0 |   0 |  0 |     0 |
| three-column   |    7 |     0 |     0 |   0 |  0 |     0 |
| timeline       |    4 |     0 |     0 |   0 |  0 |     0 |
| title          |    2 |     0 |     0 |   0 |  0 |     0 |
| toc            |    1 |     0 |     0 |   0 |  0 |     0 |
| two-column     |    5 |     0 |     0 |   0 |  0 |     0 |
| video          |    3 |     0 |     0 |   0 |  1 |     0 |

**Notes on the table:**

- **toc (1 text box)** — the fixture exercises a single TOC slide with
  no matching `section` slides, so
  `PresentationBuilder._generate_toc` populates `items` with an empty
  list and only the title shape remains. A realistic multi-slide deck
  that mixes `toc` + `section` produces one text-box-with-NAMED_SLIDE
  per entry; see `TestTocLayout::test_toc_renders_entries_and_hyperlinks`
  for that path.
- **chart (1 text box + 1 native chart)** — the chart shape is
  double-click-editable in PowerPoint (opens the embedded data table).
- **map (1 picture + 3 text boxes)** — title + "Markers" legend header
  + one text box per marker; the picture is the rasterized Leaflet
  map. Marker labels are the editable elements.
- **mermaid (1 picture + 39 chars of notes)** — the diagram source
  lives under a `--- mermaid source ---` separator in the speaker
  notes; the rendered diagram is a picture.
- **video (3 text boxes + 1 hyperlink)** — the fixture uses a remote
  URL, so the renderer emits a hyperlinked "▶ Video: Demo" label plus
  title and caption text. A local-path fixture produces a MEDIA shape
  instead (`TestVideoLayout::test_local_mp4_embeds_movie`).

## End-to-end smoke: examples/presentation.yaml

```
$ python3 -m pf pptx \
    --config examples/presentation.yaml \
    --metrics examples/metrics.json \
    --output out.pptx --editable --strict
Exporting to PowerPoint (editable)...
PPTX exported → out.pptx
$ echo $?
0
```

Inventory across the resulting 9-slide deck:

- text shapes with non-empty content: **83**
- native charts: **0** (the deck has no chart layout)
- movies: **0**
- pictures: **0**
- hyperlinks: **0**
- slides with zero editable shapes: **[]** (every slide carries
  editable content)

## Manual verification checklist (Jack)

For each layout, open `out.pptx` in PowerPoint or Keynote and confirm
the primary text can be edited in place. Tick the box, capture a
screenshot to `docs/plans/imgs/pptx-edit-<layout>.png`, and commit.

- [ ] `title` — hero title and subtitle are editable.
- [ ] `section` — section number + title + subtitle editable.
- [ ] `two-column` — title + each card's title/text editable.
- [ ] `three-column` — title + each column card editable.
- [ ] `stat-grid` — value and label strings editable per cell.
- [ ] `data-table` — section title + each table cell editable.
- [ ] `image` — title and caption editable (picture stays fixed).
- [ ] `timeline` — title + step title/description editable per step.
- [ ] `quote` — quote text and attribution editable.
- [ ] `closing` — title + subtitle editable.
- [ ] `code` — source text editable; mono font applied; per-token
  colors preserved.
- [ ] `toc` — entry labels editable; clicking an entry navigates to
  the target section slide (NAMED_SLIDE hyperlink). Test by building
  a deck with at least 2 section slides.
- [ ] `chart` — chart is double-click-editable (opens data table);
  accent colors applied to the first series.
- [ ] `map` — marker labels in the right-edge legend are editable;
  map tile raster remains fixed.
- [ ] `mermaid` — title editable; open notes pane and confirm the
  `--- mermaid source ---` separator + diagram source is present.
- [ ] `video` — for a remote URL: caption label editable, clicking
  the label opens the URL. For a local path: video plays in PowerPoint.

## Reproducing the automated inventory

The table above was generated by building a one-slide fixture per
layout (fixtures mirror `tests/test_pptx_native.py::_LAYOUT_FIXTURES`),
exporting with `--editable`, and inspecting via `python-pptx`. To
regenerate after a renderer change, re-run
`tests/test_pptx_native.py::test_each_layout_editable` — that test
enforces `≥1 editable shape` per layout as a coverage gate and uses
the same fixtures. A new layout without a renderer immediately turns
the gate red.
