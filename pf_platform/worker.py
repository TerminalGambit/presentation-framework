"""Synchronous build job wrapping PresentationBuilder."""

from pathlib import Path


def run_build(deck_dir: Path, base_url: str | None = None) -> dict:
    """Build a presentation deck from deck_dir and return result info.

    Returns dict with slide_count, warnings, contrast_warnings on success,
    or {"error": str} on failure.
    """
    try:
        from pf.builder import PresentationBuilder

        builder = PresentationBuilder(
            config_path=str(deck_dir / "presentation.yaml"),
            metrics_path=str(deck_dir / "metrics.json"),
        )
        builder.build(output_dir=str(deck_dir / "slides"), base_url=base_url)

        slides_dir = deck_dir / "slides"
        slide_count = len(list(slides_dir.glob("slide_*.html")))

        return {
            "slide_count": slide_count,
            "warnings": getattr(builder, "_warnings", []),
            "contrast_warnings": getattr(builder, "_contrast_warnings", []),
        }
    except Exception as e:
        return {"error": str(e)}
