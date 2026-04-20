# MAF Integration Contract — PF v0.3 spike

**Status:** Frozen for v0.3. Changes after this file is merged require Jack's
approval (plan trigger **AH-G4**) because downstream code, tests, and the
`video-maf` layout template are generated against it.

**Scope:** Defines the integration surface between Presentation Framework
(PF) and the Minimal Animation Framework (MAF). MAF is an external
subprocess; PF never imports it. The spike in this milestone (Phase 3 of
PF v0.3) implements the PF side of this contract against a stubbed `maf`
binary; a future PF release (v0.4 or v0.5) will close the loop against a
real tagged MAF build without modifying this contract.

**Cross-references:** PF SPEC.md §7 (Phase 3 — MAF integration spike),
PF PLAN.md T3.1.

---

## 1. `video-maf` layout — YAML contract

The `video-maf` layout is opt-in behind a theme-level feature flag:

```yaml
theme:
  experimental:
    maf_video: true  # default: false; when false the layout is inert
```

A slide using the layout looks like:

```yaml
- layout: video-maf
  data:
    manifest_path: maf/explainer.maf.yaml   # OR inline_spec, not both
    inline_spec: ~                          # MAF manifest embedded as a dict
    poster: assets/explainer-poster.png     # optional local PNG/JPG
    caption: "How the scheduler preempts"   # optional; surfaces in HTML
                                            # caption and in PPTX fallback
    cache_key_strategy: auto                # auto | manual
    cache_key: sha256:deadbeef...           # required iff strategy == manual
    caption_output: inline                  # inline | srt-only | vtt-only
```

**Field semantics:**

- `manifest_path` *(string, path)* — relative to the presentation YAML's
  directory. Either `manifest_path` or `inline_spec` is required;
  setting both is a fatal config error (raises a Click exception at
  build time).
- `inline_spec` *(mapping)* — a MAF manifest inlined into the YAML.
  When provided, PF serializes it to a temporary file before invoking
  `maf render`. The serialized form is what feeds the cache key (see §3).
- `poster` *(string, path)* — local PNG/JPG used as (1) the HTML
  `<video poster="…">` attribute, (2) the PPTX fallback still frame when
  MAF is unavailable. Remote URLs are rejected to keep the build
  hermetic.
- `caption` *(string)* — caption text shown under the video in HTML and
  under the poster in PPTX fallback. Independent of the `.srt`/`.vtt`
  tracks MAF itself produces — those carry time-aligned captions; this
  field is a one-line human title.
- `cache_key_strategy` *(enum: auto | manual)* — `auto` derives the key
  from the manifest + MAF version + env digest (§3). `manual` is an
  escape hatch for deterministic fixtures (CI, golden tests); PF uses
  the provided `cache_key` verbatim without consulting manifest bytes.
- `cache_key` *(string)* — required when `cache_key_strategy == manual`;
  must match the regex `^sha256:[0-9a-f]{64}$`.
- `caption_output` *(enum: inline | srt-only | vtt-only; default: inline)*
  — selects which MAF-produced caption file PF wires into the HTML
  `<track>` element. `inline` uses `.vtt` if present, else `.srt`.

No other fields are read from `data`. Unknown fields are logged as
build warnings but do not fail the build.

---

## 2. PF → MAF subprocess call

When the flag is on and `data.layout == "video-maf"`, PF invokes:

```
maf render <resolved-manifest-path> \
    --quiet \
    --json \
    --out <per-slide cache directory>
```

**Exact argv:** `["maf", "render", manifest_path, "--quiet", "--json",
"--out", cache_dir]`. No shell, no interpolation.

**Timeout:** 5 minutes (300 seconds). Exceeding the timeout is treated
as a rendering failure and degrades per §5.2.

**Working directory:** the cache directory (created if absent). This
keeps MAF's relative output paths predictable.

### 2.1 `maf` binary discovery

PF locates the `maf` binary via `shutil.which("maf")`. If `which` returns
`None`, the slide degrades per §5.1 without spawning a subprocess.

### 2.2 Expected stdout JSON

On success (`maf render` exits 0), PF reads the entire stdout and parses
it as JSON with this shape:

```json
{
  "render_result": {
    "manifest_sha256": "…",
    "maf_version": "0.1.0",
    "duration_seconds": 12.4,
    "warnings": []
  },
  "artifacts": {
    "mp4": "out/scene.mp4",
    "srt": "out/scene.srt",
    "vtt": "out/scene.vtt"
  }
}
```

- `render_result.maf_version` is treated as the effective version for
  the cache key (§3), not whatever `maf --version` returns.
- Artifact paths are relative to the `--out` directory. PF resolves them
  via `Path(cache_dir) / artifact_path`.
- `artifacts.srt` and `artifacts.vtt` are optional; `artifacts.mp4` is
  required. Missing `mp4` is a rendering failure per §5.2.
- Additional top-level keys are ignored. MAF is free to add fields.
- Any other shape is a contract violation and is logged as a build
  warning while the slide degrades to the poster fallback.

### 2.3 stderr taxonomy

`maf render` may write to stderr whether it succeeds or fails. PF does
not require a machine-readable stderr format; it captures stderr and
surfaces a truncated (≤200 character) preview in the build warning
when the subprocess exits non-zero. Conventional MAF stderr prefixes:

- `ERROR:` — fatal; PF degrades per §5.2.
- `WARN:` — non-fatal; PF forwards the warning to its
  `_warnings` list and continues.
- Anything else is logged verbatim in the degradation warning without
  special handling.

---

## 3. Cache key formula

```
cache_key = sha256(
    manifest_bytes
    + b"\x00"
    + maf_version.encode("utf-8")
    + b"\x00"
    + env_digest
)
```

**Components:**

- `manifest_bytes` — the **exact bytes** read from the resolved manifest
  file. For `inline_spec`, PF serializes to YAML with `sort_keys=True`
  and encodes as UTF-8 before hashing. Trailing newlines are included.
- `maf_version` — the `render_result.maf_version` returned by MAF on
  the *previous* successful render; on a cold cache PF optimistically
  uses the empty string for the pre-flight key and updates the cache
  directory name once `maf render` returns. This means a cold run
  always produces a cache entry; subsequent runs match it.
- `env_digest` — the sha256 of the concatenation of the lowercase
  platform string, the Python executable's major.minor version, and
  the content of the `MAF_CACHE_SALT` env var if set (empty string
  otherwise). Example: `darwin-arm64\x003.12\x00`. This exists so that
  a switch between x86_64 and arm64 (or between Python minor versions)
  invalidates the cache — MAF's own output may differ across platforms.

**Cache layout on disk:**

```
.pf-cache/maf/<cache_key>/
    scene.mp4
    scene.srt
    scene.vtt
    render_result.json       # copy of the stdout JSON, verbatim
```

`.pf-cache/` is added to `.gitignore` by the v0.3 Phase 3 work; users
can check it in if they want offline builds.

Cache hits skip the subprocess entirely and resolve template paths
directly from the cached artifacts.

---

## 4. PPTX fallback contract

Per spec §7.4 the `video-maf` PPTX renderer is **image-based** — no
editability beyond the caption and the link target.

**Happy path (mp4 present in cache):**

- Slide carries a `add_movie` MEDIA shape pointing at the cached `.mp4`
  (local path, embedded into the .pptx) with the `poster` as the
  preview frame.
- Caption text box under the movie shape, editable.

**Fallback path (cache miss + subprocess unavailable):**

- Poster image (`add_picture`) at the video frame location, or a dark
  placeholder rectangle if poster is missing.
- Editable text box with "▶ Video: `<caption>`" styled like the
  plain-video layout (§T2.7). Its shape-level `click_action.hyperlink`
  points at `manifest_path` (so the deck reader knows where the source
  lives).

**Strict mode (`pf pptx --strict`):**

- Happy path: no fallback event.
- Fallback path: records `{slide_index, "video-maf", "maf unavailable;
  rendered poster fallback"}` in the fallback list so `--strict` exits 1.

---

## 5. Graceful degradation

When `theme.experimental.maf_video == false`, no degradation logic is
entered — the rest of this section applies only to the flag-on case.

### 5.1 `maf` binary missing

- Detect via `shutil.which("maf") is None` before subprocess invocation.
- Emit a build warning: `"maf binary not on PATH; rendering poster
  fallback for slide N"`.
- Produce a static slide with the poster image + caption; HTML has no
  `<video>` element, only an `<img>`.
- PPTX: see §4 fallback path.
- Exit code: 0 (the deck still builds). Only `--strict` on the PPTX
  path promotes this to exit 1.

### 5.2 `maf render` exits non-zero

- Emit a build warning with the exit code and truncated stderr.
- Same poster-fallback behavior as §5.1.
- The slide's cache directory is **not** persisted — a future rerun
  retries MAF from scratch rather than blacklisting the manifest.

### 5.3 `manifest_path` missing

- **Fail-fast.** This is a spec-level error, not an environmental one.
- Raise `click.ClickException` with the resolved path and the slide
  index.
- No partial build output. The previously-successful slides are left
  in place from the prior `pf build` run (no cleanup pass).

---

## 6. Pinned target version

**v0.3 spike target:** stubbed `maf` binary only.

- Per Appendix A, D6 of PLAN.md: MAF's own `docs/PLAN.md` is at Phase 0
  scaffolding as of 2026-04-20 and has no tagged release. Gating the
  v0.3 spike on a tagged MAF build would push Phase 3 out of the
  milestone.
- The spike test (`tests/test_video_maf.py`) monkeypatches `PATH` to
  include `tests/fixtures/video-maf-placeholder/` where a shell script
  named `maf` mimics `maf render` by echoing the documented stdout JSON
  and copying pre-baked `.mp4`/`.srt`/`.vtt` artifacts.

**Future release target (v0.4 or v0.5):** `maf >= 0.1.0`.

- Once MAF ships its first tagged release, PF runs this same contract
  against the real binary — no code changes on PF's side, only the
  stub fixture is retired from the integration test (or kept as a
  no-network CI fallback).
- If MAF's JSON shape drifts between pre-alpha and v0.1.0, that's a
  **contract break** and requires a PF patch release: the contract
  document moves to `docs/archive/` with a new version in its place.

---

## 7. Explicit non-goals

Directly from SPEC §7.4 — these are out of scope for the v0.3 spike
and MUST NOT be implemented even if incidentally cheap:

- **No Docker wrapping.** MAF owns its containerization story. PF
  shells out to the binary on the host's PATH.
- **No live-reload for MAF slides.** `pf serve --watch` treats a
  `video-maf` slide as a one-shot render; changing the manifest
  requires a manual `pf build` to refresh the cache.
- **No PPTX editability for MAF slides beyond poster + link + caption.**
  The mp4 / caption tracks embed as-is; there is no "open the video's
  timeline in PowerPoint" path.

Any request to relax these must update the contract and re-trigger
Jack's review (AH-G4).

---

## 8. Change log

| Date       | Author        | Change                                      |
| ---------- | ------------- | ------------------------------------------- |
| 2026-04-20 | autonomous T3.1 | Initial draft; reviewed by Jack before T3.2 |
