"""Room-based WebSocket connection manager for presenter sync."""

import json
from typing import Dict, Set

from fastapi import WebSocket


class ConnectionManager:
    """Manages WebSocket rooms keyed by deck_id. Last-writer-wins for slide position."""

    def __init__(self):
        self.rooms: Dict[str, Set[WebSocket]] = {}
        self.state: Dict[str, int] = {}  # deck_id -> current_slide

    async def connect(self, deck_id: str, ws: WebSocket):
        """Accept WebSocket connection and add to room. Send current slide state."""
        await ws.accept()
        self.rooms.setdefault(deck_id, set()).add(ws)
        slide = self.state.get(deck_id, 1)
        await ws.send_json({"slide": slide, "type": "sync"})

    def disconnect(self, deck_id: str, ws: WebSocket):
        """Remove WebSocket from room."""
        room = self.rooms.get(deck_id)
        if room:
            room.discard(ws)
            if not room:
                del self.rooms[deck_id]

    async def broadcast(self, deck_id: str, message: dict):
        """Send message to all connections in a room. Clean up broken connections."""
        dead = []
        for ws in list(self.rooms.get(deck_id, set())):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(deck_id, ws)

    def set_slide(self, deck_id: str, slide: int):
        """Update canonical slide position (last-writer-wins)."""
        self.state[deck_id] = slide

    @property
    def room_count(self) -> int:
        return len(self.rooms)

    def connections_in_room(self, deck_id: str) -> int:
        return len(self.rooms.get(deck_id, set()))


manager = ConnectionManager()


SYNC_SCRIPT = """
<script>
(function() {
  var syncUrl = window.__PF_SYNC_URL;
  if (!syncUrl) return;
  var ws = new WebSocket(syncUrl);
  ws.onmessage = function(e) {
    var msg = JSON.parse(e.data);
    if (msg.type === 'goto' || msg.type === 'sync') {
      if (typeof show === 'function') show(msg.slide, true);
    }
  };
  var _origShow = window.show;
  if (_origShow) {
    window.show = function(n, instant, allFrags) {
      _origShow(n, instant, allFrags);
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({slide: n}));
      }
    };
  }
})();
</script>
""".strip()
