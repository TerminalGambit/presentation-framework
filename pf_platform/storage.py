"""UUID-keyed directory management for deck files."""

import shutil
import uuid
from pathlib import Path

STORE_DIR = Path("data")


def init_storage(store_dir: Path | None = None) -> Path:
    """Create the data directory and return it."""
    target = store_dir if store_dir is not None else STORE_DIR
    target.mkdir(parents=True, exist_ok=True)
    return target


def store_deck(
    config_bytes: bytes,
    metrics_bytes: bytes,
    store_dir: Path | None = None,
) -> tuple[str, Path]:
    """Store config + metrics in a new UUID-keyed directory.

    Returns (deck_id, deck_dir).
    """
    target = store_dir if store_dir is not None else STORE_DIR
    target.mkdir(parents=True, exist_ok=True)

    deck_id = str(uuid.uuid4())
    deck_dir = target / deck_id
    deck_dir.mkdir(parents=True)

    (deck_dir / "presentation.yaml").write_bytes(config_bytes)
    (deck_dir / "metrics.json").write_bytes(metrics_bytes)

    return deck_id, deck_dir


def get_deck_dir(deck_id: str, store_dir: Path | None = None) -> Path | None:
    """Return the deck directory for deck_id, or None if it doesn't exist."""
    target = store_dir if store_dir is not None else STORE_DIR
    deck_dir = target / deck_id
    return deck_dir if deck_dir.exists() else None


def delete_deck(deck_id: str, store_dir: Path | None = None) -> bool:
    """Remove the deck directory. Returns True if removed, False if not found."""
    deck_dir = get_deck_dir(deck_id, store_dir)
    if deck_dir is None:
        return False
    shutil.rmtree(deck_dir)
    return True


def get_slides_dir(deck_id: str, store_dir: Path | None = None) -> Path | None:
    """Return the slides output directory if the build exists, else None."""
    deck_dir = get_deck_dir(deck_id, store_dir)
    if deck_dir is None:
        return None
    slides_dir = deck_dir / "slides"
    return slides_dir if slides_dir.exists() else None
