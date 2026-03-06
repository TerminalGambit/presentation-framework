"""Sanitize LLM-generated content before it reaches Jinja2 templates.

This module provides XSS-hardening utilities for content produced by
language models. The primary entry point is ``safe_llm_text()`` which
strips dangerous HTML tags while preserving allowed formatting markup.

When ``bleach`` is installed (``pip install 'pf[llm]'``), it is used for
robust HTML sanitization. If bleach is not available, a conservative
regex-based fallback is applied that strips ``<script>``, ``<style>``,
``<iframe>``, ``<object>``, and ``<embed>`` tags.

Note: This module must NOT import from ``pf.builder`` — it is a
standalone utility with no internal dependencies.
"""

from __future__ import annotations

import copy
import re

# HTML tags that are safe to preserve in slide content
ALLOWED_TAGS = ["b", "i", "em", "strong", "a", "br", "p", "ul", "li", "code", "pre"]

# Attributes allowed on specific tags
ALLOWED_ATTRS: dict[str, list[str]] = {"a": ["href", "title"]}

# Tags that are always dangerous and must be stripped
_DANGEROUS_TAGS = ["script", "style", "iframe", "object", "embed"]

# Compiled regex for the fallback sanitizer — strips dangerous element pairs
# and any orphan opening/closing dangerous tags
_DANGEROUS_ELEMENT_RE = re.compile(
    r"<(?P<tag>" + "|".join(_DANGEROUS_TAGS) + r")[^>]*>.*?</(?P=tag)>",
    flags=re.DOTALL | re.IGNORECASE,
)
_ORPHAN_OPEN_TAG_RE = re.compile(
    r"<(?:" + "|".join(_DANGEROUS_TAGS) + r")[^>]*>",
    flags=re.IGNORECASE,
)
_ORPHAN_CLOSE_TAG_RE = re.compile(
    r"</(?:" + "|".join(_DANGEROUS_TAGS) + r")[^>]*>",
    flags=re.IGNORECASE,
)


def safe_llm_text(value: str) -> str:
    """Sanitize a string of LLM-generated text before rendering in templates.

    Strips dangerous HTML (script, style, iframe, object, embed) while
    preserving allowed formatting markup (b, i, em, strong, a, br, p,
    ul, li, code, pre).

    Uses ``bleach.clean()`` when available; falls back to regex stripping
    when bleach is not installed.

    Args:
        value: Raw string from LLM output.

    Returns:
        Sanitized string safe for insertion into Jinja2 templates.
    """
    if not isinstance(value, str):
        return value  # type: ignore[return-value]

    try:
        import bleach  # type: ignore[import]

        return bleach.clean(
            value,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRS,
            strip=True,
        )
    except ImportError:
        # Fallback: strip dangerous elements with regex
        result = _DANGEROUS_ELEMENT_RE.sub("", value)
        result = _ORPHAN_OPEN_TAG_RE.sub("", result)
        result = _ORPHAN_CLOSE_TAG_RE.sub("", result)
        return result


def sanitize_slide_data(data: dict | list | str | object) -> dict | list | str | object:
    """Recursively sanitize all string values in a slide data structure.

    Walks nested dicts and lists, applying ``safe_llm_text()`` to every
    string value. Non-string leaf values (int, float, bool, None) are
    passed through unchanged.

    The input is NOT mutated — a sanitized copy is returned.

    Args:
        data: A dict, list, string, or scalar value (typically the
              ``data`` sub-dict from a slide definition, or the entire
              ``metrics`` dict).

    Returns:
        A new object with the same structure but all string values
        sanitized.
    """
    if isinstance(data, dict):
        return {key: sanitize_slide_data(value) for key, value in data.items()}
    if isinstance(data, list):
        return [sanitize_slide_data(item) for item in data]
    if isinstance(data, str):
        return safe_llm_text(data)
    # Scalars (int, float, bool, None, etc.) — pass through unchanged
    return copy.copy(data) if hasattr(data, "__copy__") else data
