"""SQLite-backed analytics event store for presentation view tracking."""

import sqlite3
from pathlib import Path

# ---------------------------------------------------------------------------
# Database path (module-level, overridable for tests)
# ---------------------------------------------------------------------------

DB_PATH: Path = Path("data/analytics.db")

# ---------------------------------------------------------------------------
# JS beacon script injected into platform-served decks
# ---------------------------------------------------------------------------

BEACON_SCRIPT = """
<script>
(function() {
  var analyticsUrl = window.__PF_ANALYTICS_URL;
  var deckId = window.__PF_DECK_ID;
  if (!analyticsUrl || !deckId) return;
  var slideStart = Date.now();
  var currentSlide = 1;
  function sendEvent(slideIdx, durationMs) {
    navigator.sendBeacon(analyticsUrl,
      new Blob([JSON.stringify({deck_id: deckId, slide: slideIdx, duration_ms: durationMs})],
      {type: 'application/json'}));
  }
  document.addEventListener('visibilitychange', function() {
    if (document.visibilityState === 'hidden') sendEvent(currentSlide, Date.now() - slideStart);
  });
  var _origShow = window.show;
  if (_origShow) {
    window.show = function(n, instant, allFrags) {
      sendEvent(currentSlide, Date.now() - slideStart);
      currentSlide = n; slideStart = Date.now();
      _origShow(n, instant, allFrags);
    };
  }
})();
</script>
""".strip()


# ---------------------------------------------------------------------------
# Database initialisation
# ---------------------------------------------------------------------------


def init_db(db_path: Path | None = None) -> None:
    """Create the slide_events table if it does not exist.

    Args:
        db_path: Optional path to the SQLite database file.
                 Defaults to the module-level DB_PATH.
    """
    target = db_path if db_path is not None else DB_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(target) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS slide_events (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                deck_id     TEXT    NOT NULL,
                slide_idx   INTEGER NOT NULL,
                duration_ms INTEGER NOT NULL,
                ts          REAL    DEFAULT (unixepoch('now', 'subsec'))
            )
            """
        )
        conn.commit()


# ---------------------------------------------------------------------------
# Event recording
# ---------------------------------------------------------------------------


def record_event(
    deck_id: str,
    slide_idx: int,
    duration_ms: int,
    db_path: Path | None = None,
) -> None:
    """Insert a slide view event.

    Calls init_db() first so the table always exists (idempotent).

    Args:
        deck_id:     Identifier for the deck being viewed.
        slide_idx:   1-based slide index (as reported by the JS beacon).
        duration_ms: Time spent on the slide in milliseconds.
        db_path:     Optional path override for testing.
    """
    target = db_path if db_path is not None else DB_PATH
    init_db(target)
    with sqlite3.connect(target) as conn:
        conn.execute(
            "INSERT INTO slide_events (deck_id, slide_idx, duration_ms) VALUES (?, ?, ?)",
            (deck_id, slide_idx, duration_ms),
        )
        conn.commit()


# ---------------------------------------------------------------------------
# Dashboard aggregation
# ---------------------------------------------------------------------------


def get_dashboard(
    deck_id: str,
    db_path: Path | None = None,
) -> list[dict]:
    """Return per-slide engagement aggregations for a deck.

    Args:
        deck_id: Identifier for the deck.
        db_path: Optional path override for testing.

    Returns:
        List of dicts with keys: slide_idx, views, total_ms, avg_ms.
        Ordered by slide_idx ascending.
    """
    target = db_path if db_path is not None else DB_PATH
    init_db(target)
    with sqlite3.connect(target) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            """
            SELECT
                slide_idx,
                COUNT(*)        AS views,
                SUM(duration_ms) AS total_ms,
                AVG(duration_ms) AS avg_ms
            FROM slide_events
            WHERE deck_id = ?
            GROUP BY slide_idx
            ORDER BY slide_idx
            """,
            (deck_id,),
        )
        return [dict(row) for row in cursor.fetchall()]


def get_total_views(
    deck_id: str,
    db_path: Path | None = None,
) -> int:
    """Return the total number of slide view events recorded for a deck.

    Args:
        deck_id: Identifier for the deck.
        db_path: Optional path override for testing.

    Returns:
        Integer count of all events for the deck.
    """
    target = db_path if db_path is not None else DB_PATH
    init_db(target)
    with sqlite3.connect(target) as conn:
        cursor = conn.execute(
            "SELECT COUNT(*) FROM slide_events WHERE deck_id = ?",
            (deck_id,),
        )
        row = cursor.fetchone()
        return row[0] if row else 0
