"""Tests for the pf_platform WebSocket presenter sync (ConnectionManager + /ws/{deck_id})."""

import threading
import time

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("starlette")

from starlette.testclient import TestClient

from pf_platform.api import app
from pf_platform.sync import manager


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_manager():
    """Clear manager state before and after each test to avoid cross-test contamination."""
    manager.rooms.clear()
    manager.state.clear()
    yield
    manager.rooms.clear()
    manager.state.clear()


@pytest.fixture()
def client():
    """Shared TestClient — all WebSocket connections must use the same instance
    so they share the same ASGI event loop and can interact via the manager singleton."""
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_new_joiner_receives_current_slide(client):
    """A fresh connection to an unknown deck receives slide=1 as the default."""
    with client.websocket_connect("/ws/test-deck") as ws:
        msg = ws.receive_json()
        assert msg == {"slide": 1, "type": "sync"}


def test_joiner_after_state_set(client):
    """A client joining after state is set receives the current slide position."""
    manager.state["deck-b"] = 5
    with client.websocket_connect("/ws/deck-b") as ws:
        msg = ws.receive_json()
        assert msg["slide"] == 5
        assert msg["type"] == "sync"


def test_broadcast_slide_position(client):
    """Sending a slide position from one client broadcasts goto to all room members.

    Two clients connect to the same deck using the same TestClient instance (required
    so they share the ASGI event loop). Client 1 sends a slide change; both receive it.
    """
    received_by_client2 = []
    barrier = threading.Barrier(2, timeout=5)

    def client2_worker():
        with client.websocket_connect("/ws/deck-a") as ws2:
            # Consume the initial sync message
            ws2.receive_json()
            # Signal client 2 is ready
            barrier.wait()
            # Wait for the broadcast
            msg = ws2.receive_json()
            received_by_client2.append(msg)

    t = threading.Thread(target=client2_worker, daemon=True)
    t.start()

    with client.websocket_connect("/ws/deck-a") as ws1:
        # Consume the initial sync message
        ws1.receive_json()
        # Wait until client 2 is connected and ready
        barrier.wait()
        # Send the slide change
        ws1.send_json({"slide": 3})
        # Client 1 should also receive the broadcast
        msg1 = ws1.receive_json()
        assert msg1 == {"slide": 3, "type": "goto"}

    t.join(timeout=5)
    assert received_by_client2 == [{"slide": 3, "type": "goto"}]


def test_disconnect_cleanup(client):
    """Disconnected clients are cleaned up from the room."""
    with client.websocket_connect("/ws/deck-c") as ws:
        ws.receive_json()  # consume sync
        assert manager.connections_in_room("deck-c") == 1
    # After context exit, the WebSocket is closed and disconnect() runs
    assert manager.connections_in_room("deck-c") == 0


def test_independent_rooms(client):
    """Clients in different rooms do not receive each other's slide changes."""
    received_by_room2 = []
    room2_connected = threading.Event()

    def room2_worker():
        with client.websocket_connect("/ws/room2") as ws_b:
            ws_b.receive_json()  # consume sync
            room2_connected.set()
            # Room 2 should NOT receive anything further — use a short timeout
            # The test will close this connection after room1 is done

    t = threading.Thread(target=room2_worker, daemon=True)
    t.start()
    room2_connected.wait(timeout=5)

    with client.websocket_connect("/ws/room1") as ws_a:
        ws_a.receive_json()  # consume sync
        ws_a.send_json({"slide": 7})
        msg = ws_a.receive_json()
        assert msg == {"slide": 7, "type": "goto"}

    t.join(timeout=5)

    # Verify state isolation: room1 has slide 7, room2 state is unset
    assert manager.state.get("room1") == 7
    assert "room2" not in manager.state
    assert len(received_by_room2) == 0


def test_last_writer_wins(client):
    """The last client to send a slide position sets the canonical state."""
    barrier_start = threading.Barrier(2, timeout=5)
    barrier_done = threading.Barrier(2, timeout=5)

    def client2_worker():
        with client.websocket_connect("/ws/deck-d") as ws2:
            ws2.receive_json()  # consume sync
            barrier_start.wait()
            # Client 1 sends slide 3 first; client 2 sends slide 5 after
            ws2.send_json({"slide": 5})
            ws2.receive_json()  # consume broadcast for slide 5
            barrier_done.wait()

    t = threading.Thread(target=client2_worker, daemon=True)
    t.start()

    with client.websocket_connect("/ws/deck-d") as ws1:
        ws1.receive_json()  # consume sync
        ws1.send_json({"slide": 3})
        ws1.receive_json()  # consume broadcast for slide 3
        barrier_start.wait()
        # Wait for client 2 to send its slide
        barrier_done.wait()

    t.join(timeout=5)
    # Last writer (client 2 sent slide 5) should win
    assert manager.state.get("deck-d") == 5
