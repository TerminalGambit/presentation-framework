"""
CLI for the Presentation Framework.

Commands:
  pf init <name>   — Scaffold a new presentation project
  pf build         — Build slides from presentation.yaml + metrics.json
  pf serve         — Start a local dev server to preview slides
"""

import http.server
import json
import functools
import webbrowser
import zipfile
from pathlib import Path

import click
import yaml

from pf.builder import PresentationBuilder

STARTER_CONFIG = {
    "meta": {
        "title": "My Presentation",
        "authors": ["Your Name"],
        "institution": "",
        "date": "",
    },
    "theme": {
        "primary": "#1C2537",
        "accent": "#C4A962",
        "fonts": {
            "heading": "Playfair Display",
            "subheading": "Montserrat",
            "body": "Lato",
        },
    },
    "slides": [
        {
            "layout": "title",
            "data": {
                "title": "My Presentation",
                "subtitle": "A Subtitle",
                "tagline": "Built with Presentation Framework",
                "features": [
                    {"icon": "rocket", "label": "Feature 1", "sub": "Description"},
                    {"icon": "chart-line", "label": "Feature 2", "sub": "Description"},
                    {"icon": "gem", "label": "Feature 3", "sub": "Description"},
                ],
            },
        },
        {
            "layout": "closing",
            "data": {
                "title": "Thank You",
                "subtitle": "Questions & Discussion",
            },
        },
    ],
}

STARTER_METRICS = {
    "metadata": {"generated_at": "", "version": "1.0"},
    "summary": {},
}


@click.group()
def cli():
    """Presentation Framework — generate branded HTML slide decks."""
    pass


@cli.command()
@click.argument("name")
def init(name: str):
    """Scaffold a new presentation project."""
    project_dir = Path(name)

    if project_dir.exists():
        click.echo(f"Error: directory '{name}' already exists.", err=True)
        raise SystemExit(1)

    project_dir.mkdir(parents=True)
    (project_dir / "slides").mkdir()

    # Write starter config
    config_path = project_dir / "presentation.yaml"
    config_path.write_text(yaml.dump(STARTER_CONFIG, default_flow_style=False, sort_keys=False), encoding="utf-8")

    # Write starter metrics
    metrics_path = project_dir / "metrics.json"
    metrics_path.write_text(json.dumps(STARTER_METRICS, indent=2), encoding="utf-8")

    click.echo(f"Created presentation project: {name}/")
    click.echo(f"  {name}/presentation.yaml  — deck configuration")
    click.echo(f"  {name}/metrics.json        — data for slides")
    click.echo(f"  {name}/slides/             — output (after build)")
    click.echo(f"\nNext: edit presentation.yaml, then run 'pf build' from inside {name}/")


@cli.command()
@click.option("--config", "-c", default="presentation.yaml", help="Path to presentation.yaml")
@click.option("--metrics", "-m", default="metrics.json", help="Path to metrics.json")
@click.option("--output", "-o", default="slides", help="Output directory for built slides")
@click.option("--open", "open_browser", is_flag=True, default=False, help="Open present.html in browser after build")
def build(config: str, metrics: str, output: str, open_browser: bool):
    """Build slides from presentation.yaml + metrics.json."""
    config_path = Path(config)
    if not config_path.exists():
        click.echo(f"Error: config file '{config}' not found.", err=True)
        click.echo("Run 'pf init <name>' to create a new project, or specify --config path.")
        raise SystemExit(1)

    builder = PresentationBuilder(config_path=config, metrics_path=metrics)
    out = builder.build(output_dir=output)

    slide_count = len(list(out.glob("slide_*.html")))
    click.echo(f"Built {slide_count} slides → {out}/")

    present_path = out.resolve() / "present.html"
    if open_browser:
        webbrowser.open(f"file://{present_path}")
        click.echo(f"Opened {present_path} in browser.")
    else:
        click.echo(f"Open {out}/present.html in a browser to present.")


@cli.command()
@click.option("--dir", "-d", "directory", default="slides", help="Directory to serve")
@click.option("--port", "-p", default=8080, help="Port number")
def serve(directory: str, port: int):
    """Start a local HTTP server to preview slides."""
    serve_dir = Path(directory)
    if not serve_dir.exists():
        click.echo(f"Error: directory '{directory}' not found. Run 'pf build' first.", err=True)
        raise SystemExit(1)

    click.echo(f"Serving {directory}/ at http://localhost:{port}")
    click.echo(f"Open http://localhost:{port}/present.html to present.")
    click.echo("Press Ctrl+C to stop.\n")

    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(serve_dir))
    server = http.server.HTTPServer(("", port), handler)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        click.echo("\nServer stopped.")


@cli.command(name="zip")
@click.option("--dir", "-d", "directory", default="slides", help="Slides directory to zip")
@click.option("--output", "-o", default=None, help="Output zip path (default: <dir>.zip)")
def zip_cmd(directory: str, output: str | None):
    """Package built slides into a shareable .zip file."""
    slides_dir = Path(directory)
    if not slides_dir.exists():
        click.echo(f"Error: directory '{directory}' not found. Run 'pf build' first.", err=True)
        raise SystemExit(1)

    if not (slides_dir / "present.html").exists():
        click.echo(f"Error: '{directory}/present.html' not found — is this a built slides directory?", err=True)
        raise SystemExit(1)

    zip_path = Path(output) if output else slides_dir.with_suffix(".zip")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in sorted(slides_dir.rglob("*")):
            if file.is_file():
                arcname = file.relative_to(slides_dir.parent)
                zf.write(file, arcname)

    size_kb = zip_path.stat().st_size / 1024
    click.echo(f"Zipped → {zip_path} ({size_kb:.0f} KB)")


if __name__ == "__main__":
    cli()
