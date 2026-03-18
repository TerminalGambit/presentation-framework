# Animation System — Design Spec
**Date:** 2026-03-18
**Status:** Approved (rev 2)

---

## Overview

Add five progressive-enhancement animation features to the presentation framework. All features are opt-in via `theme.animations: true` in `presentation.yaml`, with per-element or per-block overrides via data attributes and YAML flags. The system degrades gracefully — disabling `theme.animations` leaves decks identical to today.

---

## Architecture

### Separation of concerns

| Layer | Responsibility |
|-------|---------------|
| `theme/animations.js` | Count-up counters + highlight pulse — runs inside each slide iframe on `DOMContentLoaded` |
| `present.html.j2` | Slide transition wipe — CSS + JS in the outer frame shell |
| `chart.html.j2` | Plotly chart entry animation — inline in the chart template's existing `<script>` block |
| Template changes | `reveal: step` on data-table emits `.pf-fragment` on `<tr>` rows via macro param |
| `components.css` | `@keyframes pf-pulse` keyframe + `tr.pf-fragment` transform override |

### Activation

`theme.animations: true` is the global toggle. It controls:
1. Whether `animations.js` is `<script>`-included in `base.html.j2`
2. Whether `data-count-up` attributes are emitted on `.stat-value` spans
3. Whether Plotly charts use animated entry
4. `transition_style` default becomes `"wipe"` (can still be overridden)

Individual overrides:
- `reveal: step` on a table block → sequential row reveal (works independently of `theme.animations`)
- `highlight: true` on a stat object → `data-highlight="primary"` on that stat's value span
- `animate: true` on a chart slide's `data` block → chart animation even without `theme.animations`
- `theme.transition_style: "fade" | "wipe" | "none"` → controls slide transition independently

---

## Feature Specifications

### 1. Animated Number Counters

**Where:** `theme/animations.js` + `templates/partials/stat-box.html.j2`

**Injection path:** `base.html.j2` adds the following block (alongside the existing `{% if theme.charts %}` and `{% if theme.math %}` blocks):
```html
{% if theme.animations %}
<script src="theme/animations.js"></script>
{% endif %}
```
`animations.js` is placed in `theme/` so it is copied to the output directory automatically by the existing `shutil.copytree(THEME_DIR, theme_out)` in `builder.py` — no builder change needed for the copy.

**Macro context:** `stat-box.html.j2` is a macro partial (`templates/partials/stat-box.html.j2`). To access `theme.animations` inside the macro without changing every call site, the import in layouts that use stat boxes must use Jinja2's `with context` syntax:
```jinja
{% from "partials/stat-box.html.j2" import stat_grid with context %}
```
This makes `theme` available inside the macro. The `stat_box` macro then conditionally emits:
```html
<div class="stat-value"
  {% if theme.animations %} data-count-up="true"{% endif %}
  {% if stat.highlight %} data-highlight="primary"{% endif %}>{{ value }}</div>
```
Layouts that import `stat-box.html.j2`: `stat-grid.html.j2`, and any layout that calls `stat_grid()` — update all import lines to add `with context`.

**Parsing logic:** The display string is split into three components before animation:

```
"€135M"  → { prefix: "€",  target: 135,  suffix: "M",  decimals: 0 }
"28"     → { prefix: "",   target: 28,   suffix: "",   decimals: 0 }
"12x"    → { prefix: "",   target: 12,   suffix: "x",  decimals: 0 }
"4.2B"   → { prefix: "",   target: 4.2,  suffix: "B",  decimals: 1 }
"92%"    → { prefix: "",   target: 92,   suffix: "%",  decimals: 0 }
```

Regex: `/^([^0-9]*)(\d+\.?\d*)(.*)$/`

**Animation:** `requestAnimationFrame` loop, 900ms duration, ease-out curve (`1 - (1-t)^3`). Decimal counts in tenths. Fires once per slide load.

---

### 2. Sequential Reveal on Keypress

**Where:** `templates/partials/bar-chart.html.j2` (the `data_table` macro) + `templates/layouts/data-table.html.j2` (the call site)

**Note:** The `<tr>` rows are rendered inside the `data_table` macro in `bar-chart.html.j2`, not directly in `data-table.html.j2`. This is the correct file to modify.

**Macro change:** Add `reveal` parameter to `data_table`:
```jinja
{% macro data_table(headers, rows, winner_rows=[], total_row=none, reveal=none) %}
  ...
  {% for row in rows %}
  <tr{% if loop.index0 in winner_rows %} class="winner-row{% if reveal == 'step' %} pf-fragment{% endif %}"
     {% elif reveal == 'step' %} class="pf-fragment"{% endif %}>
```

**Call site in `data-table.html.j2`:** Pass through `block.reveal`:
```jinja
{{ data_table(block.headers, block.rows, block.winner_rows | default([]), block.total_row | default(none), block.reveal | default(none)) }}
```

**`tr.pf-fragment` CSS override:** Standard `display: table-row` does not support `transform`. Add to `components.css` to disable the translateY and use opacity-only for table rows:
```css
tr.pf-fragment         { transform: none; }
tr.pf-fragment.visible { transform: none; }
```
The opacity transition from the base `.pf-fragment` rule still applies; only the `translateY(12px)` is suppressed for rows.

**No changes to `present.html.j2`** — `revealNextFragment()` and `hideLastFragment()` already handle `.pf-fragment` elements. Backward navigation (`show(n, false, true)`) calls `revealAllFragments()` showing all rows.

**YAML example:**
```yaml
- type: table
  reveal: step
  headers: [Fund, Vintage, IRR, MOIC]
  rows:
    - [Alpinvest 2019, 2019, 18.2%, 1.4x]
    - [HarbourVest 2020, 2020, 22.1%, 1.6x]
```

---

### 3. Chart Animation (Plotly Entry)

**Where:** `templates/base.html.j2` — inside the `{% if theme.charts %}` block's `initChart()` function

**Opt-in:** `theme.animations: true` OR `animate: true` in the slide's `data` block. The `animate` flag is passed through as part of `config` in the chart template, so `chart.html.j2` passes `config.animate` and `theme.animations` (via `window.__PF_CHART_THEME.animations`) to `initChart()`.

**Supported:** `bar`, `line`. Not `pie`, `donut`, `scatter`, `area`.

**Implementation in `initChart()`:**
```js
// After building traces, check animation flag
var shouldAnimate = config.animate || t.animations;
if (shouldAnimate && (chartType === 'bar' || chartType === 'line')) {
  // Build zero traces for initial render
  var zeroTraces = traces.map(function(tr) {
    var z = Object.assign({}, tr);
    z.y = tr.y ? tr.y.map(function() { return 0; }) : tr.y;
    return z;
  });
  Plotly.newPlot(el, zeroTraces, layout, {responsive: true, displayModeBar: false});
  setTimeout(function() {
    Plotly.animate(el, { data: traces }, {
      transition: { duration: 800, easing: 'cubic-in-out' },
      frame: { duration: 800, redraw: false }
    });
  }, 80);
} else {
  Plotly.newPlot(el, traces, layout, {responsive: true, displayModeBar: false});
}
```

Multi-series bar charts work because `traces` is an array — `Plotly.animate()` with `{ data: traces }` matches traces by index. The zero-initialization loops over all series.

**Schema:** Add `animate` as an optional boolean to the chart slide `data` schema:
```json
"data": {
  "properties": {
    "animate": { "type": "boolean" }
  }
}
```

**`window.__PF_CHART_THEME` addition:** Add `animations: {{ 'true' if theme.animations else 'false' }}` to the theme object so `initChart()` can read it without requiring a separate Jinja variable.

---

### 4. Animated Slide Transitions

**Where:** `present.html.j2` — CSS `<style>` block + `show()` function

**Config:** `theme.transition_style` read in `render_navigator()` and passed to the template. Add to `render_navigator()`:
```python
transition_style = theme.get("transition_style", "wipe" if theme.get("animations") else "fade")
return template.render(
    ...,
    transition_style=transition_style,
)
```

In `present.html.j2`:
```js
const TRANSITION_STYLE = "{{ transition_style | default('fade') }}";
```

**CSS additions to `present.html.j2` `<style>` block:**
```css
#slide-frame {
  /* existing: transition: opacity 0.3s ease, transform 0s; */
  transition: opacity 0.25s ease, transform 0.25s ease;
}
/* Forward exit: slides out to the left */
#slide-frame.exiting {
  opacity: 0;
  transform: translateX(-40px) scale(0.98);
}
/* Backward exit: slides out to the right */
#slide-frame.exiting-right {
  opacity: 0;
  transform: translateX(40px) scale(0.98);
}
/* Forward enter: arrives from the right */
#slide-frame.entering {
  opacity: 0;
  transform: translateX(40px) scale(0.98);
}
/* Backward enter: arrives from the left */
#slide-frame.entering-back {
  opacity: 0;
  transform: translateX(-40px) scale(0.98);
}
```

**Updated `show()` for wipe — correct timing sequence:**
```js
function show(n, instant, showAllFragments) {
  // ... bounds check, update current, curEl, progress, slideNum ...
  const file = SLIDES[current - 1];

  if (TRANSITION_STYLE === 'wipe' && !instant) {
    const exitClass = (n > /* previous */ prevSlide) ? 'exiting' : 'exiting-right';
    const enterClass = (n > prevSlide) ? 'entering' : 'entering-back';

    frame.classList.add(exitClass);
    setTimeout(() => {
      frame.src = file;
      frame.classList.remove(exitClass);
      frame.classList.add(enterClass);

      frame.addEventListener('load', function onLoad() {
        frame.removeEventListener('load', onLoad);
        // Double rAF: first ensures the .entering state is painted,
        // second triggers the CSS transition by removing the class
        requestAnimationFrame(() => requestAnimationFrame(() => {
          frame.classList.remove(enterClass);
          if (showAllFragments) revealAllFragments();
          enableLightbox();
          enableChartModals();
        }));
      }, { once: true });
    }, 220);

  } else if (instant || TRANSITION_STYLE === 'none') {
    // ... existing instant path ...
  } else {
    // ... existing fade path ...
  }
}
```

Track `prevSlide` as a variable updated alongside `current` to determine direction.

**Direction:** Forward → exit left (`translateX(-40px)`), enter from right (`translateX(+40px)`). Backward → exit right, enter from left.

---

### 5. Highlight Pulse on Key Data Points

**Where:** `theme/animations.js` (trigger) + `theme/components.css` (keyframe)

**`--pf-accent-rgb` variable:** Added to `generate_variables_css()` in `builder.py`. The `ar`, `ag`, `ab` values are already computed there. Add one line to the `:root` block:
```python
f"  --pf-accent-rgb:     {ar}, {ag}, {ab};"
```
This lands in the generated `variables.css` for every build.

**CSS keyframe** (added to `components.css`):
```css
@keyframes pf-pulse {
  0%   { box-shadow: 0 0 0 0 rgba(var(--pf-accent-rgb), 0); }
  30%  { box-shadow: 0 0 0 8px rgba(var(--pf-accent-rgb), 0.35); color: #fff; }
  70%  { box-shadow: 0 0 0 4px rgba(var(--pf-accent-rgb), 0.15); }
  100% { box-shadow: 0 0 0 0 rgba(var(--pf-accent-rgb), 0); }
}
.pf-pulse-active {
  animation: pf-pulse 1.4s ease-out forwards;
}
```

**JS trigger in `animations.js`:**
```js
document.addEventListener('DOMContentLoaded', function() {
  // Count-up
  document.querySelectorAll('[data-count-up]').forEach(countUp);
  // Highlight pulse
  document.querySelectorAll('[data-highlight="primary"]').forEach(function(el) {
    el.classList.remove('pf-pulse-active');
    void el.offsetWidth; // force reflow to reset animation
    el.classList.add('pf-pulse-active');
  });
});
```

The `void el.offsetWidth` trick is well-established and reliable across all current browsers — it forces a synchronous style flush before re-adding the animation class.

**YAML opt-in:**
```yaml
# Stat box:
stats:
  - value: "€135M"
    label: AUM
    highlight: true

# Any element via html block:
- type: html
  content: '<span data-highlight="primary">€135M</span>'
```

---

## Files Changed / Created

| File | Change type | Summary |
|------|-------------|---------|
| `theme/animations.js` | **New** | Count-up parser + pulse trigger; runs in slide iframe on DOMContentLoaded |
| `templates/base.html.j2` | Modified | `{% if theme.animations %}<script src="theme/animations.js">` block |
| `theme/components.css` | Modified | `@keyframes pf-pulse`, `.pf-pulse-active`, `tr.pf-fragment` transform override |
| `present.html.j2` | Modified | Wipe transition CSS classes + updated `show()` with direction logic + `TRANSITION_STYLE` const |
| `templates/partials/bar-chart.html.j2` | Modified | `data_table` macro gets `reveal` param; emits `.pf-fragment` on `<tr>` when `reveal="step"` |
| `templates/layouts/data-table.html.j2` | Modified | Pass `block.reveal` through to `data_table()` call |
| `templates/partials/stat-box.html.j2` | Modified | `data-count-up` + `data-highlight` attrs in `stat_box` macro |
| Layout templates that import `stat-box.html.j2` | Modified | Import changed to `with context` to expose `theme` inside macro |
| `pf/builder.py` | Modified | `render_navigator()` passes `transition_style`; `generate_variables_css()` emits `--pf-accent-rgb` |
| `pf/schema.json` | Modified | `theme.animations` (bool), `theme.transition_style` (enum), `slide.data.animate` (bool) |

---

## New YAML API Summary

```yaml
theme:
  animations: true                  # master toggle: count-up, pulse, chart anim, wipe transition
  transition_style: "wipe"          # "fade" (default) | "wipe" | "none" — independent of animations

# Stat with count-up (auto when theme.animations: true) + highlight pulse:
stats:
  - value: "€135M"
    label: AUM
    highlight: true                 # pulse on enter; count-up is auto from theme.animations

# Table with sequential reveal (independent of theme.animations):
- type: table
  reveal: step
  headers: [...]
  rows: [...]

# Chart with per-slide animation override:
- layout: chart
  data:
    animate: true                   # works even without theme.animations
    type: bar
    labels: [...]
    values: [...]
```

---

## Demo Presentation

Located at `demo/animations-demo/`. Six slides:

| # | Layout | Feature shown |
|---|--------|--------------|
| 1 | `title` | Intro — "Animation System" with 5 feature icons |
| 2 | `stat-grid` | Count-up — 4 stats count from 0 on slide enter |
| 3 | `data-table` | Sequential reveal — 6 fund rows, one per keypress |
| 4 | `chart` | Chart animation — bar chart draws over 800ms |
| 5 | `two-column` | Highlight pulse — primary metric glows gold on enter |
| 6 | `closing` | Q&A — wipe transition visible on nav to/from this slide |

`theme.animations: true` + `theme.transition_style: "wipe"` active throughout.

---

## Out of Scope

- CSS `@keyframes` for fragments (already handled by existing `.pf-fragment` styles)
- Autoplay / timed slide advance
- Per-slide `transition_style` override (global only for now)
- Animation for `pie`, `donut`, `scatter`, `area` Plotly chart types
