"""
PDF export for Presentation Framework.
Requires: pip install presentation-framework[pdf]
"""

from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


def _render_notes_page(title: str, notes: str, slide_num: int) -> str:
    """Generate a simple HTML page for speaker notes."""
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"/>
<style>
  body {{ margin: 0; padding: 40px 60px; background: #f5f5f5; font-family: 'Helvetica Neue', Arial, sans-serif; }}
  .header {{ color: #666; font-size: 12px; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 8px; }}
  .title {{ color: #333; font-size: 24px; font-weight: 600; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 2px solid #ddd; }}
  .notes {{ color: #444; font-size: 16px; line-height: 1.8; white-space: pre-wrap; }}
</style></head>
<body>
  <div class="header">SPEAKER NOTES — SLIDE {slide_num:02d}</div>
  <div class="title">{title}</div>
  <div class="notes">{notes}</div>
</body></html>"""


def export_pdf(
    slides_dir: str,
    output_path: str,
    include_notes: bool = False,
    config: dict | None = None,
):
    """Export built slides to a single PDF file.

    Uses Playwright to render each slide and produce a PDF.
    For multi-page merging, pypdf is used if available.

    Args:
        slides_dir: Directory containing slide_*.html files.
        output_path: Path to write the output PDF.
        include_notes: If True and config is provided, interleave speaker
            notes pages after each slide that has notes.
        config: Parsed presentation config dict (needed for include_notes).
    """
    if not PLAYWRIGHT_AVAILABLE:
        raise ImportError(
            "PDF export requires Playwright. Install with:\n"
            "  pip install presentation-framework[pdf]\n"
            "  playwright install chromium"
        )

    slides_path = Path(slides_dir).resolve()
    slide_files = sorted(slides_path.glob("slide_*.html"))

    if not slide_files:
        raise FileNotFoundError(f"No slide files found in {slides_dir}")

    slides_cfg = config.get("slides", []) if config else []

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
        )

        pdf_pages = []
        for i, slide_file in enumerate(slide_files):
            page = context.new_page()
            page.goto(f"file://{slide_file}")
            page.wait_for_load_state("networkidle")
            # Wait for async content (Mermaid, Leaflet) to finish rendering
            try:
                page.wait_for_selector("[data-pf-ready]", timeout=10000)
            except Exception:
                pass  # Graceful fallback if sentinel missing (pre-Phase 1 slides)
            pdf_bytes = page.pdf(
                width="1280px",
                height="720px",
                print_background=True,
                landscape=True,
            )
            pdf_pages.append(pdf_bytes)
            page.close()

            # Speaker notes page (interleaved after each slide)
            if include_notes and i < len(slides_cfg):
                notes_text = slides_cfg[i].get("notes", "")
                if notes_text:
                    slide_title = slides_cfg[i].get("data", {}).get("title", f"Slide {i + 1}")
                    notes_html = _render_notes_page(slide_title, notes_text, i + 1)
                    notes_page = context.new_page()
                    notes_page.set_content(notes_html)
                    notes_pdf = notes_page.pdf(
                        width="1280px",
                        height="720px",
                        print_background=True,
                        landscape=True,
                    )
                    pdf_pages.append(notes_pdf)
                    notes_page.close()

        browser.close()

    # Try to merge pages with pypdf if available
    try:
        from pypdf import PdfReader, PdfWriter
        import io

        writer = PdfWriter()
        for pdf_data in pdf_pages:
            reader = PdfReader(io.BytesIO(pdf_data))
            for pg in reader.pages:
                writer.add_page(pg)

        with open(output_path, "wb") as f:
            writer.write(f)
    except ImportError:
        # Fall back: write first slide only
        with open(output_path, "wb") as f:
            f.write(pdf_pages[0])
