"""FastAPI platform API for building and serving presentation decks."""

import asyncio
import functools
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from pf_platform.analytics import (
    BEACON_SCRIPT,
    get_dashboard,
    get_total_views,
    init_db,
    record_event,
)
from pf_platform.storage import delete_deck, get_deck_dir, store_deck
from pf_platform.sync import manager

# ---------------------------------------------------------------------------
# Rate limiter
# ---------------------------------------------------------------------------

limiter = Limiter(key_func=get_remote_address)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="Presentation Platform API", version="1.0.0")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS — allow all origins so embedded iframes and API clients work
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Embed headers middleware
# ---------------------------------------------------------------------------


class EmbedHeadersMiddleware(BaseHTTPMiddleware):
    """Set frame-ancestors CSP header on /d/* deck responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/d/"):
            response.headers["Content-Security-Policy"] = "frame-ancestors *"
        return response


app.add_middleware(EmbedHeadersMiddleware)

# ---------------------------------------------------------------------------
# Pydantic response models
# ---------------------------------------------------------------------------


class BuildResponse(BaseModel):
    deck_id: str
    url: str
    slide_count: int
    warnings: list = []


class ValidateResponse(BaseModel):
    valid: bool
    errors: list[str] = []


class EmbedResponse(BaseModel):
    deck_id: str
    iframe_html: str
    url: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Track which deck_ids have been mounted so we don't duplicate mounts
_mounted_decks: set[str] = set()


def _mount_deck(deck_id: str, slides_dir: Path) -> None:
    """Mount deck's slides directory under /d/{deck_id} if not already done."""
    if deck_id not in _mounted_decks:
        app.mount(
            f"/d/{deck_id}",
            StaticFiles(directory=str(slides_dir), html=True),
            name=f"deck-{deck_id}",
        )
        _mounted_decks.add(deck_id)


# ---------------------------------------------------------------------------
# API routes (registered BEFORE any StaticFiles mounts to avoid route capture)
# ---------------------------------------------------------------------------


@app.post("/api/build", response_model=BuildResponse)
@limiter.limit("10/minute")
async def build_deck(request: Request, config: UploadFile, metrics: UploadFile):
    """Build a presentation deck from uploaded config + metrics files."""
    # Read bytes immediately — UploadFile may be closed before the executor runs
    config_bytes = await config.read()
    metrics_bytes = await metrics.read()

    deck_id, deck_dir = store_deck(config_bytes, metrics_bytes)

    # Run the synchronous build in a thread pool executor
    from pf_platform.worker import run_build

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        functools.partial(run_build, deck_dir, base_url=f"/d/{deck_id}"),
    )

    if "error" in result:
        raise HTTPException(status_code=422, detail=result["error"])

    # Mount the built slides directory
    slides_dir = deck_dir / "slides"
    _mount_deck(deck_id, slides_dir)

    return BuildResponse(
        deck_id=deck_id,
        url=f"/d/{deck_id}/present.html",
        slide_count=result["slide_count"],
        warnings=result.get("warnings", []),
    )


@app.post("/api/validate", response_model=ValidateResponse)
@limiter.limit("30/minute")
async def validate_config(request: Request, config: UploadFile):
    """Validate a presentation config YAML file."""
    config_bytes = await config.read()

    # Write to temp file so PresentationBuilder can read it
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as tmp:
        tmp.write(config_bytes)
        tmp_path = tmp.name

    try:
        from pf.builder import PresentationBuilder

        builder = PresentationBuilder(config_path=tmp_path)
        builder.load_config()
        errors = builder.validate_config()
    except Exception as e:
        errors = [str(e)]
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return ValidateResponse(valid=len(errors) == 0, errors=errors)


@app.get("/api/decks/{deck_id}/embed", response_model=EmbedResponse)
async def embed_deck(deck_id: str):
    """Return an iframe HTML snippet for embedding a built deck."""
    deck_dir = get_deck_dir(deck_id)
    if deck_dir is None:
        raise HTTPException(status_code=404, detail="Deck not found")

    url = f"/d/{deck_id}/present.html"
    iframe_html = (
        f'<iframe src="{url}" width="1280" height="720" allowfullscreen '
        f'style="border:none;max-width:100%;aspect-ratio:16/9;"></iframe>'
    )
    return EmbedResponse(deck_id=deck_id, iframe_html=iframe_html, url=url)


@app.delete("/api/decks/{deck_id}")
async def remove_deck(deck_id: str):
    """Delete a built deck and its files."""
    removed = delete_deck(deck_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Deck not found")
    _mounted_decks.discard(deck_id)
    return {"deleted": deck_id}


# ---------------------------------------------------------------------------
# WebSocket presenter sync
# ---------------------------------------------------------------------------


@app.websocket("/ws/{deck_id}")
async def presenter_sync(websocket: WebSocket, deck_id: str):
    """Real-time presenter sync: any client's slide change broadcasts to all room members."""
    await manager.connect(deck_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            if "slide" in data:
                slide = int(data["slide"])
                manager.set_slide(deck_id, slide)
                await manager.broadcast(deck_id, {"slide": slide, "type": "goto"})
    except WebSocketDisconnect:
        manager.disconnect(deck_id, websocket)
    except Exception:
        manager.disconnect(deck_id, websocket)
