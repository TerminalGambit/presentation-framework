# Phase 3: LLM Integration - Research

**Researched:** 2026-03-06
**Domain:** LLM structured output, content density optimization, Jinja2 security hardening, web accessibility
**Confidence:** HIGH (core stack verified via official docs and PyPI)

## Summary

Phase 3 adds three capabilities to the presentation framework: (1) machine-readable JSON Schema per layout so LLMs can generate slide data without overflow, (2) a `generate_presentation` MCP tool backed by `instructor` for structured output, and (3) Jinja2 autoescape hardening to prevent XSS when LLM-generated content hits templates. Two supporting capabilities round out the phase: an algorithmic slide splitter (`pf/optimizer.py`) that uses the existing `LayoutAnalyzer` to redistribute overflowing content, and an accessibility audit pass that adds ARIA labels and alt-text generation.

The existing codebase provides strong foundations. `LayoutAnalyzer` already has per-block height models (`SIZE_MODEL`) and overflow detection logic — the optimizer simply needs to call those methods and redistribute blocks. The MCP server already has the `build_presentation`, `validate_config`, `get_layout_example`, and `list_layouts` tools; `generate_presentation` and `suggest_layout` extend that pattern. The `PresentationBuilder` currently uses `autoescape=False` globally — hardening means wrapping LLM-submitted content paths with `select_autoescape` or explicitly escaping values before Jinja2 renders them.

The standard stack is: `instructor>=1.13.0` with `instructor[anthropic]` extra for Claude, `pydantic>=2.0` for LLM-facing models (already available for `jsonschema` is separate), and `bleach>=6.0` for HTML sanitization of any LLM-authored HTML fields. No additional testing frameworks are required — `pytest` + `tmp_path` is the established pattern with 308 tests already collected.

**Primary recommendation:** Add `pf[llm]` optional dependency group (`instructor[anthropic]`, `bleach`) in `setup.py`. New modules are `pf/llm_schemas.py` (Pydantic constraint models), `pf/optimizer.py` (slide splitter), and extensions to `pf/mcp_server.py` (two new tools). Autoescaping hardening is a targeted change in `pf/builder.py` and affected layout templates.

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| LLM-01 | Each layout has a documented JSON Schema with constraints (maxItems, maxLength) for LLM structured output | Pydantic v2 `Field(max_length=N)` on `list` fields generates `maxItems` in JSON Schema; `model_json_schema()` exports it for LLMs |
| LLM-02 | MCP server provides `generate_presentation(prompt, style, length)` tool that outputs valid YAML+JSON | `instructor.from_provider()` with `response_model=PresentationOutput` wraps any LLM; existing MCP tool pattern applies |
| LLM-03 | MCP server provides slide suggestion tool (given partial deck, suggests next slides based on content flow) | `suggest_layout()` MCP tool: `instructor` extracts a list of `SlideSuggestion` models from prompt + current deck context |
| LLM-04 | Multi-agent workflow (researcher → data → layout → review) is documented and tested | Pattern documented in README/docstring + integration test exercising the sequence via MCP tools |
| LLM-05 | Content density optimizer auto-splits overflowing slides and redistributes content across layouts | `LayoutAnalyzer.analyze_slide()` already detects overflow; optimizer bisects column blocks into two balanced slides |
| LLM-06 | Accessibility checker validates ARIA labels, generates alt text, and supports high-contrast mode toggle | Post-render HTML scan via BeautifulSoup or regex; high-contrast mode is a CSS class toggle on `slide-container` |
| LLM-07 | Jinja2 templates use selective autoescaping for LLM-generated content to prevent XSS | `select_autoescape` on the Jinja2 `Environment` or explicit `bleach.clean()` + `Markup()` wrapping before rendering |
</phase_requirements>

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| instructor | >=1.13.0 | Structured LLM output via Pydantic response_model | 3M+ monthly downloads, Mode.TOOLS works with OpenAI + Anthropic, automatic retry on validation failure |
| pydantic | >=2.0 | Per-layout constraint models (`BaseModel` + `Field`) | Already in project (jsonschema is separate); `model_json_schema()` produces spec-compliant JSON Schema |
| bleach | >=6.0 | HTML sanitization of LLM-authored content before `|safe` | Allowlist-based, maintained through 2025 (6.3.0 released 2025-10-27) |
| anthropic | >=0.40 | Claude provider for instructor | Project is Claude-adjacent; `instructor[anthropic]` pulls it in |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| openai | >=1.0 | OpenAI provider for instructor | If user wants GPT-4o instead of Claude |
| markupsafe | (transitive, Jinja2 dep) | `Markup()` wrapper to mark sanitized HTML safe | Wrapping bleach output before rendering |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| instructor | pydantic-ai | pydantic-ai is newer with multi-agent built-in, but instructor has wider provider coverage and is more stable at 1.13+ |
| bleach | nh3 (Rust-backed) | nh3 is faster but has less Python-ecosystem mindshare; bleach is the conventional choice |
| instructor | LLM native structured output | Claude and GPT-4o support native JSON schemas, but instructor adds automatic retry + validation layer that eliminates hallucinated structures |

**Installation:**
```bash
# Core LLM extra (added to setup.py)
pip install "instructor[anthropic]>=1.13.0" "bleach>=6.0"

# Or via the new optional group:
pip install "presentation-framework[llm]"
```

---

## Architecture Patterns

### Recommended Project Structure
```
pf/
├── llm_schemas.py      # Per-layout Pydantic models with cardinality constraints
├── optimizer.py        # Slide splitter — uses LayoutAnalyzer internally
├── mcp_server.py       # Existing — add generate_presentation, suggest_layout
├── builder.py          # Existing — harden autoescape for LLM rendering path
└── schema.json         # Existing — NOT modified (used for YAML validation, not LLM output)
```

### Pattern 1: Per-Layout Pydantic Schema (`pf/llm_schemas.py`)

**What:** Pydantic `BaseModel` classes, one per layout, with `Field(max_length=N)` on string fields and `Field(max_length=N)` on list fields. `model_json_schema()` produces the LLM-consumable schema.

**When to use:** Called by `generate_presentation` MCP tool as `response_model`; also exposed via new `get_layout_schema(layout_name)` MCP tool.

**Example:**
```python
# Source: https://docs.pydantic.dev/latest/concepts/fields/
from typing import Annotated
from pydantic import BaseModel, Field

class CardBlock(BaseModel):
    type: str = Field(default="card", frozen=True)
    title: str = Field(max_length=60)
    text: str = Field(max_length=200)
    bullets: list[str] = Field(default_factory=list, max_length=4)
    # max_length=4 on list → JSON Schema "maxItems": 4

class TwoColumnSlide(BaseModel):
    layout: str = Field(default="two-column", frozen=True)
    title: str = Field(max_length=80)
    subtitle: str = Field(default="", max_length=120)
    left: list[CardBlock] = Field(max_length=3)   # maxItems: 3
    right: list[CardBlock] = Field(max_length=3)

# Export for LLM consumption:
schema = TwoColumnSlide.model_json_schema()
```

**Critical note on Pydantic v2 list constraints:** `Field(max_length=N)` on a `list[T]` field generates `"maxItems": N` in JSON Schema. This is separate from `Field(max_length=N)` on a `str` field, which generates `"maxLength": N`. The LLM sees these constraints in the schema and respects them. Instructor also sends them in field descriptions as a belt-and-suspenders approach.

### Pattern 2: `generate_presentation` MCP Tool

**What:** New FastMCP tool in `mcp_server.py` that uses `instructor.from_provider()` to call an LLM, returning a complete `PresentationOutput` (validated YAML config + metrics dict).

**When to use:** Called by an agent that has a presentation topic and wants a complete initial deck without manual YAML authoring.

**Example:**
```python
# Source: https://python.useinstructor.com/integrations/anthropic/
import instructor
from pydantic import BaseModel, Field

class PresentationOutput(BaseModel):
    yaml_config: str = Field(description="Full presentation.yaml content")
    metrics: dict = Field(description="metrics.json data as dict")

@mcp.tool()
def generate_presentation(
    prompt: str,
    style: str = "modern",
    length: str = "medium",  # short=5, medium=8, long=12 slides
    provider: str = "anthropic/claude-opus-4-6",
) -> dict:
    """Generate complete presentation YAML + metrics from a topic prompt."""
    try:
        client = instructor.from_provider(provider, mode=instructor.Mode.TOOLS)
        result = client.create(
            response_model=PresentationOutput,
            max_tokens=4096,
            messages=[{"role": "user", "content": GENERATE_SYSTEM_PROMPT.format(
                prompt=prompt, style=style, length=length
            )}],
        )
        return {"yaml_config": result.yaml_config, "metrics": result.metrics}
    except Exception as e:
        return {"error": str(e)}
```

### Pattern 3: Content Density Optimizer (`pf/optimizer.py`)

**What:** Pure-Python module that takes an overflowing slide dict and returns a list of two (or more) non-overflowing slide dicts. Uses `LayoutAnalyzer` height constants.

**When to use:** Called by `optimize_slide` MCP tool; can also be called by `generate_presentation` post-processing loop.

**Key algorithm:**
```python
from pf.analyzer import LayoutAnalyzer, USABLE_HEIGHT

def split_slide(slide: dict) -> list[dict]:
    """
    Bisect column blocks so that each split slide fits within USABLE_HEIGHT.
    Returns [slide_a, slide_b] for two-column; more splits for extreme overflow.
    """
    import copy
    layout = slide.get("layout")
    data = slide.get("data", {})

    if layout == "two-column":
        left = data.get("left", [])
        right = data.get("right", [])
        # Find split index: largest prefix that fits USABLE_HEIGHT
        left_a, left_b = _fit_split(left)
        right_a, right_b = _fit_split(right)
        slide_a = copy.deepcopy(slide)
        slide_b = copy.deepcopy(slide)
        slide_a["data"]["left"] = left_a
        slide_a["data"]["right"] = right_a
        slide_b["data"]["left"] = left_b
        slide_b["data"]["right"] = right_b
        slide_b["data"]["subtitle"] = slide["data"].get("subtitle", "") + " (cont.)"
        return [s for s in [slide_a, slide_b] if _has_content(s)]
    # Similar for three-column
    return [slide]

def _fit_split(blocks: list) -> tuple[list, list]:
    """Return (fits, remainder) where fits fills up to USABLE_HEIGHT."""
    running = 0
    for i, block in enumerate(blocks):
        h = LayoutAnalyzer.estimate_block_height(block)
        gap = 10 if i > 0 else 0
        if running + gap + h > USABLE_HEIGHT:
            return blocks[:i], blocks[i:]
        running += gap + h
    return blocks, []
```

### Pattern 4: Jinja2 Autoescape Hardening (LLM-07)

**What:** The existing `autoescape=False` global in `PresentationBuilder.__init__` is correct for the core build path (trusted author content). The LLM rendering path needs sanitization at the Python level before content reaches Jinja2.

**When to use:** Any rendering path that processes content submitted via the `generate_presentation` MCP tool or any future API endpoint.

**Two-layer approach:**
1. Sanitize LLM-generated string fields with `bleach.clean()` before they enter the template context.
2. Mark sanitized strings as `Markup()` so Jinja2 will not double-escape them.

```python
# Source: https://bleach.readthedocs.io/en/latest/clean.html
from markupsafe import Markup
import bleach

ALLOWED_TAGS = ["b", "i", "em", "strong", "a", "br", "p", "ul", "li", "code"]
ALLOWED_ATTRS = {"a": ["href", "title"]}

def sanitize_llm_html(text: str) -> Markup:
    """Clean LLM-authored HTML and return a safe Markup object."""
    cleaned = bleach.clean(text, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS, strip=True)
    return Markup(cleaned)
```

**Alternative (no bleach):** Use `select_autoescape` on a second `Environment` instance dedicated to LLM-sourced templates, with `autoescape=True`. The core build `Environment` stays `autoescape=False`.

```python
# Source: https://jinja.palletsprojects.com/en/stable/api/#jinja2.select_autoescape
from jinja2 import select_autoescape, Environment

llm_env = Environment(
    loader=...,
    autoescape=select_autoescape(enabled_extensions=("html",), default_for_string=True),
)
```

**Decision needed by planner:** bleach sanitization (more permissive, allows some HTML) vs. full autoescape (safer, strips all HTML structure). Given that LLM output goes into a slide presentation, not a browser-facing app, sanitization + Markup is the lighter-weight approach.

### Anti-Patterns to Avoid

- **Separate JSON Schema per layout in `schema.json`:** The existing `schema.json` validates the full YAML config structure. Do NOT add LLM cardinality constraints there — it would break existing YAML configs that have more items than LLM-safe limits. The Pydantic schemas in `pf/llm_schemas.py` are LLM-only.
- **Using `conlist()` (Pydantic v1 style):** Pydantic v2 uses `list[T] = Field(max_length=N)` not the legacy `conlist()`. The `conlist()` function still works but generates poor type checker support.
- **Calling `instructor.from_provider()` at module load time:** Requires LLM credentials at import. Use lazy init inside the MCP tool function, guarded by `try/except ImportError`.
- **Global autoescape=True in builder.py:** Would break all existing templates that use `{{ slide.data.title }}` without `|safe` — those currently rely on `autoescape=False` because titles are trusted author input. Only sanitize LLM-sourced paths.
- **Storing LLM API keys in metrics.json or presentation.yaml:** These are potentially committed files. Key management must be environment variable only.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| LLM response validation + retry | Custom JSON parsing loop | `instructor` | Handles partial responses, schema mismatch retry, streaming — 10+ edge cases |
| HTML sanitization | Regex tag stripping | `bleach` | Regex-based HTML parsing misses malformed tags, nested structures, attribute injection |
| Pydantic JSON Schema export | Manual schema dict | `model.model_json_schema()` | Automatic, correct `$defs` for nested models, `maxItems`/`maxLength` wired up |
| LLM provider abstraction | `if provider == "openai": ...` branching | `instructor.from_provider(provider_str)` | Handles 15+ providers with identical API |

**Key insight:** Content overflow splitting is actually the only algorithm worth hand-rolling — because it depends on `LayoutAnalyzer.SIZE_MODEL` constants that are project-specific and not generalizable.

---

## Common Pitfalls

### Pitfall 1: `maxItems` vs `maxLength` on Pydantic list fields
**What goes wrong:** Using `conlist(min_length=0, max_length=4)` or the wrong Pydantic field generates `maxLength` instead of `maxItems` in JSON Schema. An LLM that sees `maxLength: 4` on a list interprets it as a string constraint.
**Why it happens:** Pydantic v2 uses `max_length` for both strings and lists, but the JSON Schema keyword differs: `maxLength` for strings, `maxItems` for lists.
**How to avoid:** Use `list[T] = Field(max_length=N)` not `Annotated[list[T], Field(max_length=N)]` — verify output with `Model.model_json_schema()` and confirm `"maxItems"` appears, not `"maxLength"`.
**Warning signs:** `model_json_schema()` shows `"maxLength"` on an array field.

### Pitfall 2: instructor import fails silently in MCP context
**What goes wrong:** `generate_presentation` MCP tool raises `ImportError` if `pf[llm]` is not installed, which corrupts the stdio JSON-RPC channel.
**Why it happens:** FastMCP tools are invoked at call time; if the import is at the top of `mcp_server.py`, it fails on server start.
**How to avoid:** Lazy import inside the tool function with `try/except ImportError` that returns `{"error": "LLM features require: pip install 'pf[llm]'"}`.

### Pitfall 3: Slide splitter produces empty slides
**What goes wrong:** `split_slide()` returns a slide_b with empty columns when the overflow is just one large block.
**Why it happens:** The split algorithm moves the last block to slide_b, but if slide_a has 1 item and it overflows alone, slide_b is empty.
**How to avoid:** If a single block exceeds USABLE_HEIGHT, don't split — emit an overflow warning instead. Add `_has_content(slide)` guard before appending to output list.

### Pitfall 4: Autoescaping breaks existing builds
**What goes wrong:** Changing `autoescape=False` to `autoescape=True` in `PresentationBuilder.__init__` causes all existing slide titles, subtitles, and bullet text to escape HTML entities — `&amp;` appears in output.
**Why it happens:** Existing YAML authors write `"Revenue &amp; Costs"` expecting it to pass through; with autoescape=True, `&` becomes `&amp;amp;`.
**How to avoid:** Do NOT change the global `autoescape` setting. Apply sanitization only in the LLM code path, not in `PresentationBuilder`.

### Pitfall 5: MCP tool blocks if instructor makes synchronous HTTP calls
**What goes wrong:** `generate_presentation` hangs the MCP server for 10-30 seconds during LLM call, blocking all other tool calls.
**Why it happens:** FastMCP's default is synchronous; one slow tool blocks the event loop.
**How to avoid:** Mark the tool `async` and use `await asyncio.to_thread(client.create, ...)` or use instructor's async client (`instructor.from_provider(...).async_client`).

### Pitfall 6: Alt text generation for images requires external LLM call
**What goes wrong:** LLM-06 accessibility requirement says "generates alt text" — this implies an LLM API call per image at build time.
**Why it happens:** Genuine alt text requires understanding the image content, which is a vision model task.
**How to avoid:** Alt text "generation" for Phase 3 should mean: (a) warn when `<img>` lacks `alt`, and (b) use a filename-derived fallback (e.g., `alt="photo.jpg"` → `alt="photo"`) or accept a `description` field in the YAML. Full vision-based generation is a deferred enhancement.

---

## Code Examples

Verified patterns from official sources:

### Instructor with Anthropic (provider string API)
```python
# Source: https://python.useinstructor.com/integrations/anthropic/
import instructor
from pydantic import BaseModel, Field

class SlideTitle(BaseModel):
    title: str = Field(max_length=80, description="Slide title, max 80 chars")
    subtitle: str = Field(default="", max_length=120)

client = instructor.from_provider(
    "anthropic/claude-opus-4-6",
    mode=instructor.Mode.TOOLS,
)

result = client.create(
    response_model=SlideTitle,
    max_tokens=256,
    messages=[
        {"role": "user", "content": "Generate a title slide for a talk on AI in finance."}
    ],
)
# result.title and result.subtitle are validated strings
```

### Pydantic v2 list constraint → JSON Schema maxItems
```python
# Source: https://docs.pydantic.dev/latest/concepts/fields/
from pydantic import BaseModel, Field

class TimelineSlide(BaseModel):
    layout: str = Field(default="timeline", frozen=True)
    title: str = Field(max_length=80)
    steps: list[dict] = Field(min_length=2, max_length=6)  # JSON Schema: minItems:2, maxItems:6

import json
print(json.dumps(TimelineSlide.model_json_schema(), indent=2))
# "steps": { "type": "array", "minItems": 2, "maxItems": 6, ... }
```

### Jinja2 autoescape for string templates
```python
# Source: https://jinja.palletsprojects.com/en/stable/api/#jinja2.select_autoescape
from jinja2 import Environment, select_autoescape

# Existing builder (untouched — trusted content):
env = Environment(autoescape=False)

# LLM rendering environment (new — untrusted content):
llm_env = Environment(
    autoescape=select_autoescape(
        enabled_extensions=("html",),
        default_for_string=True,
    )
)
```

### bleach sanitization before Markup
```python
# Source: https://bleach.readthedocs.io/en/latest/clean.html
from markupsafe import Markup
import bleach

SLIDE_ALLOWED_TAGS = ["b", "i", "em", "strong", "br", "code"]
SLIDE_ALLOWED_ATTRS = {}

def safe_llm_text(value: str) -> str:
    """Sanitize an LLM-authored text field. Returns plain str (not Markup)."""
    return bleach.clean(value, tags=SLIDE_ALLOWED_TAGS, attributes=SLIDE_ALLOWED_ATTRS, strip=True)
```

### FastMCP tool with lazy LLM import
```python
# Source: existing mcp_server.py pattern + instructor pattern
@mcp.tool()
def generate_presentation(prompt: str, style: str = "modern", length: str = "medium") -> dict:
    """Generate complete presentation YAML + metrics from a topic prompt."""
    try:
        import instructor
    except ImportError:
        return {"error": "LLM features require: pip install 'pf[llm]'"}

    from pf.llm_schemas import PresentationOutput
    # ... rest of implementation
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `instructor.from_openai(OpenAI())` | `instructor.from_provider("openai/gpt-4o")` | instructor 1.x | Single API for 15+ providers |
| `conlist(item_type=str, max_items=4)` (Pydantic v1) | `list[str] = Field(max_length=4)` | Pydantic v2 | Better static analysis, `model_json_schema()` compatibility |
| `autoescape=False` globally in Jinja2 | Selective per-template or per-environment | Jinja2 2.x+ | Targeted security without breaking trusted templates |
| Manual JSON parsing of LLM output | `response_model=Model` in instructor | 2023+ | Automatic retry, validation, streaming |

**Deprecated/outdated:**
- `conlist()`, `constr()`: Pydantic v1 constrained type helpers. Still available in v2 for compatibility but discouraged — use `Annotated[..., Field(...)]` or `field: type = Field(max_length=N)` directly.
- `instructor.patch(client)`: Old patching API replaced by `instructor.from_openai(client)` and `instructor.from_provider()`.

---

## Open Questions

1. **LLM provider requirement — OpenAI or Anthropic?**
   - What we know: `instructor` supports both with `from_provider()`; the existing `mcp_server.py` is provider-agnostic.
   - What's unclear: Should `generate_presentation` default to Anthropic (project is Claude-adjacent) or remain provider-agnostic with a `provider` parameter?
   - Recommendation: Default to `"anthropic/claude-opus-4-6"` since project is built for Claude MCP, but accept `provider` param for flexibility.

2. **Alt text generation scope (LLM-06)**
   - What we know: True image alt text generation requires a vision LLM. The accessibility requirement says "generates alt text".
   - What's unclear: Does Phase 3 need live vision-based generation, or is a filename-fallback + "missing alt" warning sufficient?
   - Recommendation: Phase 3 = warn + filename fallback. Vision-based generation is a Phase 4/v2 enhancement.

3. **Suggest layout tool input format**
   - What we know: LLM-03 says "given partial deck, suggests next slides based on content flow."
   - What's unclear: Does the tool receive the full slides list, just section headings, or a plaintext summary?
   - Recommendation: Accept `slides_yaml: str` (raw YAML of current deck) + `topic: str`. Keep it simple for the first iteration.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 7.x+ |
| Config file | none — no pytest.ini or pyproject.toml; uses default discovery |
| Quick run command | `python3 -m pytest tests/test_llm_schemas.py tests/test_optimizer.py tests/test_accessibility.py -x -q` |
| Full suite command | `python3 -m pytest tests/ -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| LLM-01 | `get_layout_schema("timeline").model_json_schema()` contains `"maxItems"` for steps | unit | `python3 -m pytest tests/test_llm_schemas.py::test_timeline_schema_has_maxitems -x` | ❌ Wave 0 |
| LLM-01 | All 11 core layout schemas export valid JSON Schema with `maxItems` on list fields | unit | `python3 -m pytest tests/test_llm_schemas.py::test_all_schemas_have_constraints -x` | ❌ Wave 0 |
| LLM-02 | `generate_presentation` returns dict without "error" key when instructor is available | integration (mocked LLM) | `python3 -m pytest tests/test_mcp_server.py::TestGeneratePresentation -x` | ❌ Wave 0 |
| LLM-02 | `generate_presentation` returns helpful error when instructor not installed | unit | `python3 -m pytest tests/test_mcp_server.py::test_generate_requires_llm_extra -x` | ❌ Wave 0 |
| LLM-03 | `suggest_layout` returns non-empty list for a partial deck input | integration (mocked LLM) | `python3 -m pytest tests/test_mcp_server.py::TestSuggestLayout -x` | ❌ Wave 0 |
| LLM-04 | Multi-agent pattern documented: test that all 4 MCP tools can be called in sequence | smoke | `python3 -m pytest tests/test_multiagent_workflow.py -x` | ❌ Wave 0 |
| LLM-05 | `split_slide()` splits a two-column slide with 12 cards into two slides | unit | `python3 -m pytest tests/test_optimizer.py::test_split_two_column -x` | ❌ Wave 0 |
| LLM-05 | `split_slide()` does not produce empty slides when single block overflows | unit | `python3 -m pytest tests/test_optimizer.py::test_split_single_overflow_no_empty -x` | ❌ Wave 0 |
| LLM-05 | `optimize_slide` MCP tool returns split slides dict | unit | `python3 -m pytest tests/test_mcp_server.py::TestOptimizeSlide -x` | ❌ Wave 0 |
| LLM-06 | Accessibility checker warns when `<img>` has no `alt` attribute | unit | `python3 -m pytest tests/test_accessibility.py::test_warns_missing_alt -x` | ❌ Wave 0 |
| LLM-06 | Accessibility checker warns when interactive element has no `aria-label` | unit | `python3 -m pytest tests/test_accessibility.py::test_warns_missing_aria -x` | ❌ Wave 0 |
| LLM-07 | Builder renders LLM-submitted `<script>` tag as escaped text, not live script | unit | `python3 -m pytest tests/test_builder.py::test_llm_content_escaping -x` | ❌ Wave 0 |
| LLM-07 | `safe_llm_text()` strips `<script>` tags from input | unit | `python3 -m pytest tests/test_builder.py::test_safe_llm_text_strips_script -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `python3 -m pytest tests/test_llm_schemas.py tests/test_optimizer.py tests/test_accessibility.py tests/test_mcp_server.py -x -q`
- **Per wave merge:** `python3 -m pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_llm_schemas.py` — covers LLM-01 (all per-layout schema constraints)
- [ ] `tests/test_optimizer.py` — covers LLM-05 (split_slide algorithm, edge cases)
- [ ] `tests/test_accessibility.py` — covers LLM-06 (ARIA label scan, alt text warnings)
- [ ] `tests/test_multiagent_workflow.py` — covers LLM-04 (sequential MCP tool calls)

*(Additions to `tests/test_mcp_server.py` for LLM-02, LLM-03, LLM-05 MCP surface are in-file additions, not new files)*

---

## Sources

### Primary (HIGH confidence)
- https://python.useinstructor.com/integrations/anthropic/ — `from_provider()` API, Mode.TOOLS, Anthropic integration pattern
- https://pypi.org/project/instructor/1.8.1/ + latest — version 1.14.5 (Jan 2026), optional extras per provider
- https://docs.pydantic.dev/latest/concepts/fields/ — `Field(max_length=N)` on list fields, JSON Schema `maxItems` generation
- https://jinja.palletsprojects.com/en/stable/api/#jinja2.select_autoescape — `select_autoescape()` signature and usage
- https://bleach.readthedocs.io/en/latest/clean.html — bleach 6.3.0 (Oct 2025), `clean()` API, allowed tags/attrs

### Secondary (MEDIUM confidence)
- https://deepwiki.com/instructor-ai/instructor/2.1-installation-and-setup — install commands, extras list, verified against PyPI
- https://www.w3.org/WAI/ARIA/apg/ — WAI-ARIA Authoring Practices 1.3, ARIA label requirements for interactive elements
- https://testparty.ai/blog/carousel-slider-accessibility — Accessible carousel/slide ARIA patterns (verified against WAI-ARIA spec)

### Tertiary (LOW confidence)
- https://github.com/pydantic/pydantic/issues/9815 — Pydantic issue on `Sequence` maxLength vs maxItems — LOW confidence, issue-tracker not official docs

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — instructor version verified via PyPI (1.14.5 as of Jan 2026); bleach version verified via PyPI (6.3.0 Oct 2025); Pydantic field docs verified via official docs
- Architecture: HIGH — all patterns derived from official sources; `LayoutAnalyzer` internals verified by reading source
- Pitfalls: HIGH for Jinja2 and Pydantic (official docs); MEDIUM for instructor edge cases (based on library patterns)

**Research date:** 2026-03-06
**Valid until:** 2026-04-06 (instructor and pydantic are actively maintained; check for new minor versions before implementation)
