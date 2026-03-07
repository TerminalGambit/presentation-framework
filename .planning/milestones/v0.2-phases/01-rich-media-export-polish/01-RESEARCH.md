# Phase 1: Rich Media + Export Polish - Research

**Researched:** 2026-03-06
**Domain:** Frontend CDN integration (Highlight.js, Mermaid.js, Leaflet), Playwright async export, python-pptx native shapes
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Code block integration**
- Both a `code` block type (for two-column/three-column layouts) AND a dedicated full-slide `code` layout
- Highlight.js theme auto-matches slide background color using existing `_is_light()` detection — dark theme on dark slides, light theme on light slides
- Line numbers optional, off by default — users add `line_numbers: true` per code block
- Auto-detect from slides: builder scans for code blocks and injects Highlight.js CDN automatically — no `theme.code` flag needed

**Fragment reveal model**
- Both per-bullet and per-block granularity — `fragment: true` on a bullet reveals that bullet; on a block reveals the whole block
- Arrow keys are context-aware: right arrow reveals next fragment first, then advances to next slide when all fragments shown (reveal.js / PowerPoint model)
- Animation: fade + slide up (opacity 0→1 with subtle upward translation)
- Fragment JS state machine always included in every build (no flag, no detection — it's small enough)

**Embed authoring model**
- Mermaid: Both `mermaid` block type AND dedicated full-slide `mermaid` layout
- Video: Both `video` block type AND dedicated full-slide `video` layout — auto-detects YouTube/Vimeo/MP4 from URL
- Maps: Both `map` block type AND dedicated full-slide `map` layout — data shape includes lat, lng, zoom, markers
- All new rich media types use auto-detect for CDN loading — builder scans slides and includes only needed libraries (Highlight.js, Mermaid.js, Leaflet)
- Existing `theme.math` and `theme.charts` flags stay as-is for backward compatibility

**Export fallback strategy**
- Video in PDF/PPTX: Thumbnail image with centered play icon overlay — auto-fetch thumbnail for YouTube/Vimeo, first frame for MP4. Link to video URL in PPTX notes
- Mermaid in PDF/PPTX: Playwright renders the SVG using `data-pf-ready` sentinel — wait for Mermaid.js to finish rendering, then capture
- Maps in PDF/PPTX: Playwright screenshot of live Leaflet map — wait for tile loading, then capture
- Code in PDF/PPTX: Playwright captures the syntax-highlighted output

### Claude's Discretion
- PPTX native vs image per rich media content type — Claude picks the best trade-off (native shapes for text-heavy layouts, images for code/mermaid/maps/video as appropriate)
- Specific Highlight.js dark/light theme names
- Fragment animation timing and easing
- Mermaid theme/styling defaults
- Map tile provider choice for Leaflet
- Per-slide CSS implementation details (`style:` key parsing)
- Auto-generated TOC slide design and section detection logic

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| MEDIA-01 | Code blocks with syntax highlighting (Highlight.js) | CDN URLs verified, auto-detect pattern documented, theme selection via `_is_light()` |
| MEDIA-02 | Slide fragments for progressive reveal (bullet/block) | JS state machine pattern documented, keyboard model specified |
| MEDIA-03 | Mermaid.js diagrams in slides and exports | CDN URL verified, async `mermaid.run()` API documented, `data-pf-ready` sentinel pattern |
| MEDIA-04 | Video embed (YouTube/Vimeo/MP4) with thumbnail in HTML, static in exports | YouTube thumbnail URL pattern, Vimeo oEmbed API, MP4 iframe documented |
| MEDIA-05 | Google Maps / Leaflet embed with lat/lng, zoom, markers | Leaflet CDN verified, OpenStreetMap tile provider documented |
| MEDIA-06 | Custom per-slide CSS via `style:` key | Implementation pattern documented (inline style injection) |
| MEDIA-07 | Auto-generated TOC slide from section dividers | Section layout scan pattern and builder hook documented |
| EXPORT-01 | Async JS content renders correctly in PDF/PPTX via `data-pf-ready` sentinel | `page.wait_for_selector("[data-pf-ready]")` pattern verified in Playwright Python |
| EXPORT-02 | PPTX native renderer covers all 11 layouts | Current gap: 3 of 11 native, 8 image-fallback — expansion pattern in existing `pptx_native.py` |
| EXPORT-03 | PDF export includes speaker notes as annotations or separate pages | Two approaches documented: PDF notes via CSS `@media print`, PPTX via `notes_slide.notes_text_frame` |
| EXPORT-04 | PPTX export reuses single browser context instead of per-slide spawning | `browser.new_context()` + multiple `page` objects pattern confirmed in Playwright |
</phase_requirements>

---

## Summary

Phase 1 adds rich media capabilities (code, diagrams, video, maps, fragments) to an existing Jinja2/Python slide generator, then polishes the Playwright-based PDF and python-pptx export pipeline. The project already has the core patterns in place: conditional CDN injection in `base.html.j2` (KaTeX and Plotly), a Playwright context in `pdf.py` / `pptx.py`, and a partial native PPTX renderer (`pptx_native.py`) that handles 3 of 11 layouts natively.

The five new media types (code, mermaid, video, map, fragment) all follow the same dual pattern: a block type that can appear inside columnar layouts AND a dedicated full-slide layout. The builder must gain a pre-render scan to auto-detect which CDN libraries are needed. This is a clean extension of the existing `{% if theme.math %}` CDN pattern in `base.html.j2`.

The export gap is the most complex work. The `data-pf-ready` sentinel needs to be added to every async media template and waited on in Playwright before screenshot/PDF capture. The PPTX native renderer must be extended from 3 to 11 layouts. PDF speaker notes require a second render pass (notes page HTML template) or a Playwright-based two-page-per-slide PDF merge.

**Primary recommendation:** Build each media type as a self-contained template+block-type unit, test HTML rendering, then layer in the export handling. The sentinel pattern is the critical shared infrastructure — implement it first as it gates everything in EXPORT-01 through EXPORT-04.

---

## Standard Stack

### Core (already in project — no new installs needed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Jinja2 | 3.x (existing) | Template rendering for new layout templates | Already the template engine |
| Playwright (sync) | 1.x (existing) | PDF/PPTX screenshot capture | Already used in pdf.py, pptx.py |
| python-pptx | 1.0.0 | Native PPTX shape generation | Already used in pptx_native.py |
| PyYAML | existing | YAML config parsing | Unchanged |

### New CDN Libraries (front-end only, no pip install)
| Library | Version | CDN URL | Purpose |
|---------|---------|---------|---------|
| Highlight.js | 11.11.1 | `https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/highlight.min.js` | Code syntax highlighting |
| Highlight.js github-dark theme | 11.11.1 | `https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/styles/github-dark.min.css` | Dark slide code theme |
| Highlight.js github theme | 11.11.1 | `https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/styles/github.min.css` | Light slide code theme |
| Mermaid.js | 11.12.0 | `https://cdnjs.cloudflare.com/ajax/libs/mermaid/11.12.0/mermaid.min.js` | Diagram rendering |
| Leaflet.js | 1.9.4 | `https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js` | Interactive maps |
| Leaflet CSS | 1.9.4 | `https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css` | Map styling |

**Confidence:** HIGH — all CDN URLs verified directly against cdnjs.com (March 2026).

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Highlight.js | Prism.js | Prism is lighter but requires manual language registration; Highlight.js auto-detects |
| Leaflet + OpenStreetMap | Google Maps embed API | Google requires API key and billing; OpenStreetMap is free and requires no credentials |
| Mermaid CDN UMD | Mermaid ESM module | ESM is the future but requires `<script type="module">` and browser compatibility tradeoffs; UMD `.min.js` is simpler for CDN use |

---

## Architecture Patterns

### CDN Auto-Detect Pattern (extends existing `base.html.j2`)

The builder scans slides before render and sets flags on the template context. This mirrors the existing `theme.math` / `theme.charts` pattern but is driven by slide content, not user flags.

**In `builder.py` — new `_scan_features()` method:**
```python
def _scan_features(self, slides: list[dict]) -> dict:
    """Scan all slides and return set of required CDN features."""
    features = {"code": False, "mermaid": False, "map": False}
    for slide in slides:
        layout = slide.get("layout", "")
        data = slide.get("data", {})
        if layout == "code":
            features["code"] = True
        if layout == "mermaid":
            features["mermaid"] = True
        if layout == "map":
            features["map"] = True
        # Scan block types in columnar layouts
        for key in ("left", "right", "columns"):
            for block in data.get(key, []):
                if isinstance(block, dict):
                    t = block.get("type", "")
                    if t == "code":
                        features["code"] = True
                    elif t == "mermaid":
                        features["mermaid"] = True
                    elif t == "map":
                        features["map"] = True
    return features
```

Pass `features` into `render_slide()` and into the navigator template so `base.html.j2` can conditionally include CDNs.

**In `base.html.j2` — new blocks (parallel to existing `theme.math` block):**
```html
{% if features.code %}
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/styles/{{ 'github' if is_light else 'github-dark' }}.min.css"/>
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/highlight.min.js"></script>
<script>document.addEventListener('DOMContentLoaded', () => { hljs.highlightAll(); });</script>
{% endif %}
{% if features.mermaid %}
<script src="https://cdnjs.cloudflare.com/ajax/libs/mermaid/11.12.0/mermaid.min.js"></script>
<script>
  mermaid.initialize({ startOnLoad: false, theme: '{{ "default" if is_light else "dark" }}' });
  document.addEventListener('DOMContentLoaded', async () => {
    await mermaid.run({ querySelector: '.mermaid' });
    document.body.setAttribute('data-pf-ready', '1');
  });
</script>
{% endif %}
{% if features.map %}
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css"/>
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
{% endif %}
```

**Note:** `is_light` must be passed to render context from `builder.py` using the existing `_is_light()` function.

### `data-pf-ready` Sentinel Pattern (EXPORT-01)

Async content (Mermaid, Leaflet tile loading) must signal completion before Playwright screenshots.

**In async templates:** Set `data-pf-ready` on `<body>` after all async work completes.

For Mermaid slides:
```javascript
await mermaid.run({ querySelector: '.mermaid' });
document.body.setAttribute('data-pf-ready', '1');
```

For Leaflet map slides:
```javascript
map.on('load', () => {
  map.whenReady(() => {
    setTimeout(() => document.body.setAttribute('data-pf-ready', '1'), 500);
  });
});
```

For slides with no async content: set sentinel synchronously on `DOMContentLoaded`.

**In `pdf.py` and `pptx.py` export pipeline:**
```python
page.goto(f"file://{slide_file}")
page.wait_for_load_state("networkidle")
# For slides with async content, wait for sentinel
if slide_has_async_content:
    page.wait_for_selector("[data-pf-ready]", timeout=10000)
```

Simpler alternative: always use `page.wait_for_selector("[data-pf-ready]")` — every slide template sets it synchronously or asynchronously. This eliminates the per-slide conditional and makes the sentinel universal.

**Recommendation:** Make `data-pf-ready` universal. Every slide template sets it — synchronous slides set it on `DOMContentLoaded`, async slides set it after async work completes. Playwright always waits for it. This is the cleanest design.

### Fragment State Machine (MEDIA-02)

The fragment JS state machine lives in `present.html.j2` (the navigator), not in individual slide HTML. Individual slides mark fragments with `data-fragment` attributes.

**YAML authoring:**
```yaml
slides:
  - layout: two-column
    data:
      left:
        - type: card
          fragment: true   # whole block reveals at once
          title: Step 1
          text: First point
      right:
        - type: card
          bullets:
            - text: "Point A"
              fragment: true  # individual bullet reveals
            - text: "Point B"
              fragment: true
```

**Template rendering:**
```html
<!-- block-level fragment -->
<div class="card {% if item.fragment %}pf-fragment{% endif %}">...</div>

<!-- bullet-level fragment -->
<li class="{% if bullet.fragment %}pf-fragment{% endif %}">{{ bullet.text }}</li>
```

**CSS for initial hidden state:**
```css
.pf-fragment {
  opacity: 0;
  transform: translateY(12px);
  transition: opacity 0.35s ease, transform 0.35s ease;
}
.pf-fragment.visible {
  opacity: 1;
  transform: translateY(0);
}
```

**Navigator keyboard logic (in `present.html.j2`):**
```javascript
// On right arrow: reveal next fragment OR advance slide
function handleRight() {
  const iframe = currentSlideIframe();
  const frags = iframe.contentDocument.querySelectorAll('.pf-fragment:not(.visible)');
  if (frags.length > 0) {
    frags[0].classList.add('visible');
  } else {
    advanceSlide();
  }
}
```

### Video Embed Pattern (MEDIA-04)

**URL auto-detection in builder or template:**
```python
def _detect_video_type(url: str) -> str:
    if "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    elif "vimeo.com" in url:
        return "vimeo"
    else:
        return "mp4"

def _youtube_video_id(url: str) -> str:
    # handles both youtube.com/watch?v=ID and youtu.be/ID
    import re
    match = re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})", url)
    return match.group(1) if match else ""

def _youtube_thumbnail(video_id: str) -> str:
    return f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
```

**YouTube thumbnail URL:** `https://img.youtube.com/vi/{VIDEO_ID}/maxresdefault.jpg`
(Fall back to `hqdefault.jpg` if maxres returns 404.)

**Vimeo thumbnail:** Fetch `https://vimeo.com/api/oembed.json?url=https://vimeo.com/{VIDEO_ID}` and extract `thumbnail_url`. (Note: requires HTTP request at build time — do lazily in template or in builder pre-render pass.)

**HTML output for YouTube (click-to-play):**
```html
<div class="pf-video-embed" data-video-url="https://www.youtube.com/embed/VIDEO_ID">
  <img src="https://img.youtube.com/vi/VIDEO_ID/maxresdefault.jpg" alt="Video thumbnail"/>
  <div class="pf-play-btn"><i class="fas fa-play"></i></div>
</div>
<script>
  document.querySelector('.pf-video-embed').addEventListener('click', function() {
    var url = this.dataset.videoUrl;
    this.innerHTML = '<iframe src="' + url + '?autoplay=1" frameborder="0" allowfullscreen></iframe>';
  });
</script>
```

**PDF/PPTX export:** Playwright screenshots the thumbnail + play icon. No live iframe needed.

### Mermaid Block/Layout Pattern (MEDIA-03)

**YAML authoring:**
```yaml
# Full-slide layout
- layout: mermaid
  data:
    title: System Architecture
    diagram: |
      graph LR
        A[Browser] --> B[CDN]
        B --> C[Server]

# Block type in two-column
- layout: two-column
  data:
    left:
      - type: mermaid
        diagram: |
          sequenceDiagram
            Alice->>Bob: Hello
```

**Template (`layouts/mermaid.html.j2`):**
```html
{% extends "base.html.j2" %}
{% block content %}
{% include "partials/header.html.j2" %}
<div class="mermaid" data-diagram="{{ slide.data.diagram | e }}">
{{ slide.data.diagram }}
</div>
{% endblock %}
```

**Mermaid initialization uses `mermaid.run()` (v10+ API, verified):**
```javascript
mermaid.initialize({ startOnLoad: false, theme: 'dark' });
document.addEventListener('DOMContentLoaded', async () => {
  await mermaid.run({ querySelector: '.mermaid' });
  document.body.setAttribute('data-pf-ready', '1');
});
```

### Map Block/Layout Pattern (MEDIA-05)

**YAML authoring:**
```yaml
- layout: map
  data:
    title: Office Locations
    lat: 37.7749
    lng: -122.4194
    zoom: 12
    markers:
      - lat: 37.7749
        lng: -122.4194
        label: HQ
```

**Template initializes Leaflet:**
```javascript
const map = L.map('pf-map-{{ slide_id }}').setView([{{ slide.data.lat }}, {{ slide.data.lng }}], {{ slide.data.zoom | default(12) }});
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '© OpenStreetMap contributors',
  maxZoom: 19
}).addTo(map);
{% for marker in slide.data.markers | default([]) %}
L.marker([{{ marker.lat }}, {{ marker.lng }}]).addTo(map).bindPopup('{{ marker.label | default("") }}');
{% endfor %}
map.whenReady(() => {
  setTimeout(() => document.body.setAttribute('data-pf-ready', '1'), 800);
});
```

**Tile provider:** OpenStreetMap (`https://tile.openstreetmap.org/{z}/{x}/{y}.png`) — free, no API key needed.

### Per-Slide CSS (`style:` key) — MEDIA-06

**YAML:**
```yaml
- layout: two-column
  style: "background: linear-gradient(135deg, #1C2537, #2a3a5c);"
  data:
    title: Special Slide
```

**Template injection (in `base.html.j2` or layout templates):**
```html
<div class="slide-container" ... style="{{ density_style }}{% if slide.style %} {{ slide.style }}{% endif %}">
```

This is a one-line change in `base.html.j2`. The `slide.style` value is already available in template context since the full `slide` dict is passed.

**Security note:** `autoescape=False` is current setting. Per-slide CSS is author-controlled YAML (not user-submitted), so this is acceptable in Phase 1. XSS hardening is Phase 3.

### Auto-Generated TOC Slide (MEDIA-07)

**YAML trigger:**
```yaml
slides:
  - layout: toc  # auto-generated; builder detects section layouts
    data:
      title: Table of Contents
```

**Builder logic:** Scan `slides` list for `layout: section` entries. Collect their `data.title` and `data.number`. Inject as a list into the TOC slide's `data.items` before rendering.

```python
def _generate_toc(self, slides: list[dict]) -> list[dict]:
    """Collect section slides to build TOC entries."""
    items = []
    for slide in slides:
        if slide.get("layout") == "section":
            data = slide.get("data", {})
            items.append({
                "number": data.get("number", ""),
                "title": data.get("title", ""),
                "subtitle": data.get("subtitle", ""),
            })
    return items
```

The `toc` layout is a new Jinja2 template that renders a numbered list of sections.

### Native PPTX Expansion (EXPORT-02)

**Current state:** `pptx_native.py` has native renderers for 3 layouts: `section`, `quote`, `closing`.

**Gap:** 8 layouts need native renderers: `title`, `two-column`, `three-column`, `data-table`, `stat-grid`, `chart`, `image`, `timeline`. Plus 4 new Phase 1 layouts: `code`, `mermaid`, `video`, `map`.

**Strategy (Claude's discretion):**
- **Native (text shapes):** `title`, `section` (done), `quote` (done), `closing` (done), `stat-grid` (text + colored boxes), `two-column` (text cards), `three-column` (text cards)
- **Image fallback acceptable:** `chart`, `mermaid`, `code`, `map`, `video` — these are inherently visual/interactive and native PPTX shape fidelity is low value vs. screenshot

This reduces the native expansion to 4 new renderers: `title`, `stat-grid`, `two-column`, `three-column`. The remaining layouts stay as Playwright screenshots. The planner should plan for these 4 native renderers plus the image fallback sentinel fix.

**Shared browser context fix (EXPORT-04):**

Current `pptx.py` spawns a new browser for every build call (one `sync_playwright()` context wrap). The fix: move `browser.new_context()` outside the per-slide loop, create one page per slide within the shared context.

```python
with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context(viewport={"width": 1280, "height": 720})
    for slide_file in slide_files:
        page = context.new_page()
        page.goto(f"file://{slide_file}")
        page.wait_for_load_state("networkidle")
        page.wait_for_selector("[data-pf-ready]", timeout=10000)
        png_bytes = page.screenshot(full_page=False)
        page.close()
    browser.close()
```

This is already correct in `pptx.py` (it creates one `context` outside the loop), but EXPORT-04 is listed as a requirement because `pptx_native.py`'s `_render_image_fallback` spawns a new browser per slide. The fix is to pass a shared `page` or `context` into `_render_image_fallback`.

### PDF Speaker Notes (EXPORT-03)

**Two viable approaches:**

**Approach A — Separate notes page HTML template (RECOMMENDED)**

For each slide, render a companion `slide_NN_notes.html` page with slide title + notes text, then merge into PDF using pypdf.

```python
# In pdf.py export
for slide_file in slide_files:
    page.goto(f"file://{slide_file}")
    page.wait_for_selector("[data-pf-ready]", timeout=10000)
    pdf_bytes = page.pdf(width="1280px", height="720px", print_background=True)
    pdf_pages.append(pdf_bytes)

    if include_notes and notes_content:
        notes_file = slides_path / f"{slide_file.stem}_notes.html"
        page.goto(f"file://{notes_file}")
        notes_pdf = page.pdf(width="1280px", height="720px", print_background=True)
        pdf_pages.append(notes_pdf)
```

**Approach B — CSS `@media print` hidden section**

Add a `<div class="slide-notes-page">` to each slide HTML that is hidden by `display: none` normally but visible via `@media print`. Playwright PDF renders both. This is simpler but produces interleaved notes pages in one PDF call per slide.

**Recommendation:** Approach A, because it produces clean separate note pages and reuses the existing pypdf merge infrastructure. The `slide_NN_notes.html` template is a simple Jinja2 template showing title + notes text on a white background.

**Prerequisite:** pypdf must be installed (`pip install pypdf`) — already an optional dep.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Syntax highlighting | Custom regex tokenizer | Highlight.js 11.11.1 | 300+ languages, battle-tested, CDN, auto-detection |
| Diagram rendering | Custom SVG generator | Mermaid.js 11.12.0 | Supports 15+ diagram types, active development |
| Interactive maps | Custom tile stitching | Leaflet 1.9.4 + OpenStreetMap | Free, no API key, full-featured |
| Video URL parsing | Custom regex for YouTube/Vimeo | Simple regex + YouTube thumbnail URL pattern | YouTube thumbnail URLs are stable and well-documented |
| PDF merging | Custom PDF byte manipulation | pypdf (already optional dep) | Already in project, handles merge cleanly |
| PPTX shape placement | Pixel math from scratch | python-pptx `Inches()` / `Emu()` utilities | Already used in pptx_native.py |

**Key insight:** Every rich media type has a battle-tested JS library. The project's job is wiring these libraries into the Jinja2 template system, not rebuilding them.

---

## Common Pitfalls

### Pitfall 1: Playwright `networkidle` Is Not Enough for Mermaid/Leaflet
**What goes wrong:** `page.wait_for_load_state("networkidle")` waits for no in-flight network requests but does NOT wait for Mermaid SVG rendering or Leaflet tile compositing to finish. Screenshots will capture blank diagrams or gray tiles.
**Why it happens:** Mermaid renders asynchronously via `requestAnimationFrame` after script load. Leaflet tiles load as images (trigger network) but compositing happens after.
**How to avoid:** Implement the `data-pf-ready` sentinel as universal infrastructure. Every template sets it — synchronously for static layouts, asynchronously after completion for Mermaid/Leaflet.
**Warning signs:** PDF/PPTX screenshots show `[Object object]` text or blank boxes where diagrams should be.

### Pitfall 2: Mermaid.js ESM vs UMD Bundle
**What goes wrong:** Using `<script type="module">` with the ESM bundle (`mermaid.esm.min.mjs`) requires `import mermaid from '...'` syntax, which doesn't work if you also need to call `mermaid.initialize()` from a separate inline script.
**Why it happens:** ESM imports don't expose globals; UMD does.
**How to avoid:** Use the UMD bundle from cdnjs (`mermaid.min.js`) — it exposes `window.mermaid` as a global. The Mermaid v11 cdnjs package provides the UMD bundle.

### Pitfall 3: `_render_image_fallback` Spawns a New Browser Per Slide
**What goes wrong:** Each call to `_render_image_fallback` in `pptx_native.py` launches Chromium, creates a context, takes a screenshot, then shuts down. 20-slide deck = 20 browser launches. Very slow.
**Why it happens:** Current implementation uses `with sync_playwright() as p:` inside the fallback function.
**How to avoid:** Refactor `export_pptx_editable` to create one browser + context, pass a `context` arg into `_render_image_fallback`.

### Pitfall 4: `schema.json` Layout Enum Must Be Kept in Sync
**What goes wrong:** Adding new layouts (`code`, `mermaid`, `video`, `map`, `toc`) without updating `schema.json` causes every new slide to fail `validate_config()` with "not one of enum values."
**Why it happens:** `schema.json` has `"enum": ["title", "two-column", ...]` — explicit allowlist.
**How to avoid:** Add all new layout names to the enum before writing any layout templates. Update `schema.json` first as a dependency of every new layout plan.

### Pitfall 5: YouTube `maxresdefault.jpg` Returns 404 for Older Videos
**What goes wrong:** Some older YouTube videos don't have a `maxresdefault.jpg` thumbnail. Fetching it returns a 404 and the `<img>` shows broken image.
**Why it happens:** High-res thumbnails are only generated for newer videos.
**How to avoid:** Fall back to `hqdefault.jpg` which is always available. Pattern:
```html
<img src="https://img.youtube.com/vi/VIDEO_ID/hqdefault.jpg"
     onerror="this.src='https://img.youtube.com/vi/VIDEO_ID/hqdefault.jpg'"/>
```
Or: use `hqdefault.jpg` as default and note that `maxresdefault.jpg` is bonus resolution.

### Pitfall 6: Fragment State Lives in Navigator, Not in Slide iframe
**What goes wrong:** Fragment state (which bullets have been revealed) must survive slide transitions. If fragment state is tracked inside the slide iframe, it resets when the iframe is reloaded.
**Why it happens:** The navigator (`present.html.j2`) loads each slide in an iframe. Slide iframes can reload during transitions.
**How to avoid:** Track fragment state in the navigator JS, not in the slide iframe. The navigator sends `postMessage` commands to the iframe to reveal specific fragment indices, or the navigator drives the iframe's `.pf-fragment` classes directly via `contentDocument` access.

### Pitfall 7: Leaflet Map Tiles Fail in `file://` Protocol
**What goes wrong:** Leaflet tile requests to `https://tile.openstreetmap.org/...` may fail when the page is loaded as `file://` in Playwright due to mixed-content or CORS restrictions.
**Why it happens:** Some browsers block HTTPS requests from `file://` pages.
**How to avoid:** Use Playwright's `browser.new_context()` with no extra restrictions — Chromium allows HTTPS XHR/fetch from `file://` by default. Verify with a test. If tiles fail, the fallback is a static map image at the given lat/lng using a static maps service (or simply: accept that map tiles may not fully load in exports, which is acceptable per the "Playwright screenshot of live Leaflet map" decision).

---

## Code Examples

Verified patterns from official sources and existing project code:

### Highlight.js — CDN auto-detect injection
```html
<!-- Source: cdnjs.com verified March 2026 -->
{% if features.code %}
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/styles/{{ 'github' if is_light else 'github-dark' }}.min.css"/>
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/highlight.min.js"></script>
<script>document.addEventListener('DOMContentLoaded', () => hljs.highlightAll());</script>
{% endif %}
```

### Mermaid.js — async run + sentinel
```javascript
// Source: mermaid.js.org/config/usage.html (verified March 2026)
mermaid.initialize({ startOnLoad: false, theme: 'dark' });
document.addEventListener('DOMContentLoaded', async () => {
  await mermaid.run({ querySelector: '.mermaid' });
  document.body.setAttribute('data-pf-ready', '1');
});
```

### Playwright — sentinel wait (Python sync API)
```python
# Source: playwright.dev/python/docs/api/class-page
page.goto(f"file://{slide_file}")
page.wait_for_load_state("networkidle")
page.wait_for_selector("[data-pf-ready]", timeout=10000)
png_bytes = page.screenshot(full_page=False)
```

### python-pptx — speaker notes
```python
# Source: python-pptx.readthedocs.io/en/latest/user/notes.html
notes_slide = slide.notes_slide
notes_slide.notes_text_frame.text = slide_cfg.get("notes", "")
```

### python-pptx — native title layout renderer
```python
# Source: pptx_native.py existing pattern (project code)
def _render_title(slide, data: dict, theme: dict):
    _add_bg(slide, theme["primary"])
    center_x = SLIDE_WIDTH // 2
    # Hero title in accent color
    txBox = slide.shapes.add_textbox(
        center_x - Inches(5), Inches(1.8), Inches(10), Inches(2)
    )
    _set_text(txBox.text_frame, data["title"], theme["font_heading"],
              60, theme["accent"], bold=True)
    # Subtitle
    if data.get("subtitle"):
        txBox = slide.shapes.add_textbox(
            center_x - Inches(5), Inches(3.9), Inches(10), Inches(0.8)
        )
        _set_text(txBox.text_frame, data["subtitle"], theme["font_subheading"],
                  20, theme["text_muted"])
```

### Shared Playwright browser context (EXPORT-04 fix)
```python
# Source: playwright.dev/python/docs/api/class-browsercontext
with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context(viewport={"width": 1280, "height": 720})
    for slide_file in slide_files:
        page = context.new_page()
        page.goto(f"file://{slide_file}")
        page.wait_for_load_state("networkidle")
        page.wait_for_selector("[data-pf-ready]", timeout=10000)
        png_bytes = page.screenshot(full_page=False)
        page.close()
    browser.close()
```

### Code block YAML data shape
```yaml
# As a block type in two-column/three-column:
- type: code
  language: python   # or "auto" for auto-detect
  code: |
    def hello(name: str) -> str:
        return f"Hello, {name}!"
  line_numbers: true  # optional, default false

# As a dedicated full-slide layout:
- layout: code
  data:
    title: Builder Pattern
    language: python
    code: |
      class PresentationBuilder:
          def build(self, output_dir: str) -> Path:
              ...
    line_numbers: false
    caption: "Core build pipeline"
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `mermaid.init()` | `mermaid.run()` (promise-based) | Mermaid v10 | `run()` is awaitable — enables `data-pf-ready` sentinel pattern |
| `page.wait_for_selector()` (discouraged) | `page.wait_for_selector()` still valid in Python sync API | Playwright 1.x | The Locator API is preferred for testing but `wait_for_selector` remains valid for export scripting |
| Per-browser-launch pattern | Single shared context | N/A (always possible) | Critical for export performance |
| Image-based PPTX only | Hybrid native + image | Added in project's pptx_native.py | Enables editable text in simple layouts |

**Deprecated/outdated:**
- `mermaid.init()`: deprecated since Mermaid v10; use `mermaid.run()` with async/await
- `mermaid.startOnLoad: true`: still works but gives no control over completion timing; use `startOnLoad: false` + `await mermaid.run()`
- `page.waitForSelector()` (JS camelCase): the Python Playwright API uses `wait_for_selector` (snake_case) — not deprecated, just needs correct casing

---

## Open Questions

1. **Leaflet tiles in `file://` Playwright context**
   - What we know: Chromium generally allows HTTPS from `file://`. Leaflet uses standard `<img>` tags for tiles.
   - What's unclear: Whether Playwright's Chromium launch flags block cross-origin images from file context.
   - Recommendation: Write a test in Wave 0 that loads a Leaflet page from `file://` and checks tile count. If tiles fail, fall back to a static Google Maps or OpenStreetMap embed URL (static image, no JS required) for export-only.

2. **Vimeo thumbnail fetch at build time**
   - What we know: Vimeo oEmbed API at `https://vimeo.com/api/oembed.json?url=...` returns `thumbnail_url`.
   - What's unclear: Build environments may lack network access. Fetching thumbnails at build time adds a network dependency.
   - Recommendation: Make thumbnail fetching optional — if the HTTP request fails or times out (2s timeout), fall back to a generic "play" placeholder image. Log a warning via the existing `_warnings` mechanism.

3. **PDF speaker notes as annotations vs. separate pages**
   - What we know: Playwright `page.pdf()` generates PDF pages. pypdf can merge. PPTX notes via `notes_slide.notes_text_frame` is verified.
   - What's unclear: PDF annotations (proper annotation type, not page) would require PyMuPDF or pdfminer beyond the current pypdf dep.
   - Recommendation: Use separate notes pages (Approach A above). Avoid adding PyMuPDF dependency in Phase 1. Notes pages are simpler, more readable, and compatible with existing pypdf merge.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (existing, version in project deps) |
| Config file | None detected — uses pytest defaults |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MEDIA-01 | Code block type renders `<code>` with language class; CDN injected when code found | unit | `pytest tests/test_code_block.py -x` | ❌ Wave 0 |
| MEDIA-01 | Highlight.js CDN absent when no code slides | unit | `pytest tests/test_code_block.py::test_no_code_no_cdn -x` | ❌ Wave 0 |
| MEDIA-01 | `is_light` flag selects `github` vs `github-dark` theme | unit | `pytest tests/test_code_block.py::test_theme_selection -x` | ❌ Wave 0 |
| MEDIA-02 | `fragment: true` on block adds `pf-fragment` CSS class | unit | `pytest tests/test_fragments.py::test_block_fragment_class -x` | ❌ Wave 0 |
| MEDIA-02 | `fragment: true` on bullet adds `pf-fragment` to `<li>` | unit | `pytest tests/test_fragments.py::test_bullet_fragment_class -x` | ❌ Wave 0 |
| MEDIA-03 | Mermaid layout renders `.mermaid` div with diagram text | unit | `pytest tests/test_mermaid.py::test_mermaid_layout_renders -x` | ❌ Wave 0 |
| MEDIA-03 | Mermaid CDN injected only when mermaid slide present | unit | `pytest tests/test_mermaid.py::test_cdn_auto_detect -x` | ❌ Wave 0 |
| MEDIA-04 | YouTube URL yields thumbnail img tag with correct URL | unit | `pytest tests/test_video.py::test_youtube_thumbnail -x` | ❌ Wave 0 |
| MEDIA-04 | MP4 URL yields `<video>` element | unit | `pytest tests/test_video.py::test_mp4_embed -x` | ❌ Wave 0 |
| MEDIA-05 | Map layout renders Leaflet init script with lat/lng | unit | `pytest tests/test_map.py::test_map_renders_leaflet -x` | ❌ Wave 0 |
| MEDIA-05 | Leaflet CDN injected only when map slide present | unit | `pytest tests/test_map.py::test_cdn_auto_detect -x` | ❌ Wave 0 |
| MEDIA-06 | `style:` key on slide injects inline CSS into container | unit | `pytest tests/test_custom_style.py::test_style_key_injected -x` | ❌ Wave 0 |
| MEDIA-07 | Builder generates TOC items from section slides | unit | `pytest tests/test_toc.py::test_toc_collects_sections -x` | ❌ Wave 0 |
| EXPORT-01 | `data-pf-ready` attr present in static slide HTML | unit | `pytest tests/test_export_sentinel.py::test_sentinel_in_static_slide -x` | ❌ Wave 0 |
| EXPORT-02 | `export_pptx_editable` dispatches to native renderer for `title` layout | unit | `pytest tests/test_pptx_native.py::TestTitleLayout -x` | ❌ Wave 0 (class) |
| EXPORT-03 | `export_pdf` with `include_notes=True` produces 2x page count | integration | `pytest tests/test_pdf.py::test_pdf_with_notes -x` | ❌ Wave 0 |
| EXPORT-04 | `export_pptx_editable` does not spawn multiple browsers | unit (mock) | `pytest tests/test_pptx.py::test_single_browser_context -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/ -x -q`
- **Per wave merge:** `pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_code_block.py` — covers MEDIA-01
- [ ] `tests/test_fragments.py` — covers MEDIA-02
- [ ] `tests/test_mermaid.py` — covers MEDIA-03
- [ ] `tests/test_video.py` — covers MEDIA-04
- [ ] `tests/test_map.py` — covers MEDIA-05
- [ ] `tests/test_custom_style.py` — covers MEDIA-06
- [ ] `tests/test_toc.py` — covers MEDIA-07
- [ ] `tests/test_export_sentinel.py` — covers EXPORT-01
- [ ] Expand `tests/test_pptx_native.py` with `TestTitleLayout`, `TestTwoColumnLayout`, `TestStatGridLayout`, `TestThreeColumnLayout` — covers EXPORT-02
- [ ] Expand `tests/test_pdf.py` with `test_pdf_with_notes` — covers EXPORT-03
- [ ] Expand `tests/test_pptx.py` with `test_single_browser_context` — covers EXPORT-04

**Note:** 137 existing tests cover the baseline v0.2.0 functionality. All new tests are additive.

---

## Sources

### Primary (HIGH confidence)
- [cdnjs.com/libraries/highlight.js](https://cdnjs.com/libraries/highlight.js) — version 11.11.1 confirmed, CDN URLs verified
- [cdnjs.com/libraries/mermaid](https://cdnjs.com/libraries/mermaid) — version 11.12.0 confirmed, CDN URL verified
- [cdnjs.com/libraries/leaflet](https://cdnjs.com/libraries/leaflet) — version 1.9.4 confirmed, CDN URLs verified
- [mermaid.js.org/config/usage.html](https://mermaid.js.org/config/usage.html) — `mermaid.run()` async API confirmed, `startOnLoad: false` pattern
- [python-pptx.readthedocs.io/en/latest/user/notes.html](https://python-pptx.readthedocs.io/en/latest/user/notes.html) — `notes_slide.notes_text_frame.text` API confirmed
- [playwright.dev/python/docs/api/class-page](https://playwright.dev/python/docs/api/class-page) — `wait_for_selector("[data-pf-ready]")` pattern confirmed
- [playwright.dev/python/docs/api/class-browsercontext](https://playwright.dev/python/docs/api/class-browsercontext) — shared context pattern confirmed
- Existing project code (`pf/builder.py`, `pf/pptx_native.py`, `pf/pdf.py`, `templates/base.html.j2`) — direct read

### Secondary (MEDIUM confidence)
- [highlightjs.org/demo](https://highlightjs.org/demo) — `github-dark` and `github` theme names verified
- [YouTube IFrame Player API](https://developers.google.com/youtube/player_parameters) — embed URL format `youtube.com/embed/VIDEO_ID`
- [YouTube thumbnail URL format](https://img.youtube.com/vi/{VIDEO_ID}/hqdefault.jpg) — documented in multiple sources, stable URL pattern
- [Vimeo oEmbed API](https://vimeo.com/api/oembed.json) — `thumbnail_url` field confirmed via WebSearch

### Tertiary (LOW confidence)
- Leaflet tile behavior in Playwright `file://` context — inferred from general Chromium behavior, not directly verified; needs test

---

## Metadata

**Confidence breakdown:**
- Standard stack (CDN versions): HIGH — verified against cdnjs.com March 2026
- Architecture patterns: HIGH — based on direct reading of existing project code
- Playwright sentinel: HIGH — verified against official Playwright Python docs
- Vimeo thumbnail fetch: MEDIUM — API documented but network-at-build-time behavior not tested
- Leaflet tiles in file:// context: LOW — inferred, needs validation test

**Research date:** 2026-03-06
**Valid until:** 2026-09-06 (stable libraries — 6 months reasonable; CDN URLs may update sooner on major version bumps)
