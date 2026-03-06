"""Accessibility auditing for built slide HTML.

Checks built HTML files for common accessibility issues:
- Missing alt attributes on <img> elements
- Missing aria-label or visible text on interactive elements
- Missing role="region" on slide container
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass


@dataclass
class AccessibilityWarning:
    """A single accessibility issue found in built HTML."""

    file: str       # e.g., "slide_01.html"
    element: str    # e.g., "<img src='photo.jpg'>"
    issue: str      # e.g., "missing alt attribute"
    suggestion: str # e.g., "Add alt='Photo' based on filename"
    severity: str   # "error" or "warning"


def generate_alt_text(src: str) -> str:
    """Generate readable alt text from an image src path or URL.

    Extracts the filename, strips the extension, and converts hyphens/underscores
    to spaces with title-case formatting.

    Examples:
        "images/team-photo.jpg"          -> "Team Photo"
        "quarterly_revenue.png"          -> "Quarterly Revenue"
        "/path/to/my-image.jpg"          -> "My Image"
        "https://example.com/hero.png"   -> "Hero"
    """
    # Extract just the filename (handles both paths and URLs)
    filename = src.rstrip("/").split("/")[-1].split("?")[0]
    # Strip extension
    name, _, _ = filename.rpartition(".")
    if not name:
        name = filename
    # Replace hyphens and underscores with spaces, then title-case
    name = re.sub(r"[-_]+", " ", name).strip()
    return name.title()


def check_accessibility(html: str, filename: str = "") -> list[AccessibilityWarning]:
    """Audit an HTML string for accessibility issues.

    Checks:
    1. Missing alt attributes on <img> elements (severity: error)
    2. Missing aria-label and visible text on interactive elements (severity: warning)
    3. Missing role="region" on slide container (severity: warning)

    Returns warnings sorted by severity (errors first).
    """
    warnings: list[AccessibilityWarning] = []

    # ── 1. Check <img> elements for missing alt ───────────────────────────────
    img_pattern = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
    for img_tag in img_pattern.findall(html):
        if not re.search(r'\balt\s*=', img_tag, re.IGNORECASE):
            # Extract src for generating alt suggestion
            src_match = re.search(r'\bsrc\s*=\s*["\']([^"\']*)["\']', img_tag, re.IGNORECASE)
            src = src_match.group(1) if src_match else ""
            alt_suggestion = generate_alt_text(src) if src else "descriptive text"
            warnings.append(AccessibilityWarning(
                file=filename,
                element=img_tag[:120],
                issue="missing alt attribute",
                suggestion=f"Add alt='{alt_suggestion}' based on filename",
                severity="error",
            ))

    # ── 2. Check interactive elements for missing aria-label / visible text ───
    # Patterns for elements that need labels
    interactive_patterns = [
        (re.compile(r"<button\b([^>]*)>(.*?)</button>", re.IGNORECASE | re.DOTALL), "button"),
        (re.compile(r"<a\b([^>]*)>(.*?)</a>", re.IGNORECASE | re.DOTALL), "a"),
        (re.compile(r"<input\b([^>]*)>", re.IGNORECASE), "input"),
        (re.compile(r"<select\b([^>]*)>(.*?)</select>", re.IGNORECASE | re.DOTALL), "select"),
    ]

    for pattern, tag_name in interactive_patterns:
        for match in pattern.finditer(html):
            attrs = match.group(1)
            # Check for aria-label attribute
            has_aria_label = bool(re.search(r'\baria-label\s*=', attrs, re.IGNORECASE))
            # Check for visible text content (groups differ for self-closing vs paired tags)
            inner_text = ""
            if match.lastindex and match.lastindex >= 2:
                inner_text = re.sub(r"<[^>]+>", "", match.group(2)).strip()
            # Also check for aria-labelledby
            has_aria_labelledby = bool(re.search(r'\baria-labelledby\s*=', attrs, re.IGNORECASE))

            if not has_aria_label and not has_aria_labelledby and not inner_text:
                full_tag = match.group(0)[:120]
                warnings.append(AccessibilityWarning(
                    file=filename,
                    element=full_tag,
                    issue=f"missing aria-label or visible text on <{tag_name}>",
                    suggestion=f"Add aria-label='...' attribute to the <{tag_name}> element",
                    severity="warning",
                ))

    # ── 3. Check for role="region" on slide container ─────────────────────────
    if not re.search(r'role\s*=\s*["\']region["\']', html, re.IGNORECASE):
        warnings.append(AccessibilityWarning(
            file=filename,
            element="<div class=\"slide-container\"...>",
            issue="missing role=\"region\" on slide container",
            suggestion="Add role=\"region\" and aria-label=\"...\" to the slide-container element",
            severity="warning",
        ))

    # Sort: errors first, then warnings
    warnings.sort(key=lambda w: (0 if w.severity == "error" else 1))
    return warnings


def check_slide_dir(output_dir: str) -> list[AccessibilityWarning]:
    """Scan all slide_*.html files in output_dir and return aggregated warnings.

    Args:
        output_dir: Path to the directory containing built slide HTML files.

    Returns:
        Aggregated list of AccessibilityWarnings from all slides.
    """
    all_warnings: list[AccessibilityWarning] = []
    output_path = output_dir if isinstance(output_dir, os.PathLike) else output_dir

    try:
        entries = sorted(os.listdir(output_path))
    except FileNotFoundError:
        return all_warnings

    for filename in entries:
        if not (filename.startswith("slide_") and filename.endswith(".html")):
            continue
        filepath = os.path.join(output_path, filename)
        try:
            with open(filepath, encoding="utf-8") as f:
                html = f.read()
            warnings = check_accessibility(html, filename)
            all_warnings.extend(warnings)
        except OSError:
            continue

    return all_warnings
