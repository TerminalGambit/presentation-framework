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


def export_pdf(slides_dir: str, output_path: str, include_notes: bool = False):
    """Export built slides to a single PDF file.

    Uses Playwright to render each slide and produce a PDF.
    For multi-page merging, pypdf is used if available.
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

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            viewport={"width": 1280, "height": 720},
        )

        pdf_pages = []
        for slide_file in slide_files:
            page = context.new_page()
            page.goto(f"file://{slide_file}")
            page.wait_for_load_state("networkidle")
            pdf_bytes = page.pdf(
                width="1280px",
                height="720px",
                print_background=True,
                landscape=True,
            )
            pdf_pages.append(pdf_bytes)
            page.close()

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
