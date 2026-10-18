import json
import socket
import threading
import time
import uuid

import pytest
import uvicorn
from websockets.sync.client import connect

from app.auth import CurrentUser, get_token_checker
from app.main import app
from app.models import Profile
from app.rooms import ROOMS, Room, RoomError, scorers_allowed



def wrong_for(room):
    """A note with a different letter from every note of the current question: always wrong."""
    letters = {n[:-1] for n in room.notes}
    return [next(n for n in ["C4", "D4", "E4", "F4", "G4", "A4", "B4"] if n[:-1] not in letters)]


def make_room(players=2, category="easy", target=1000):
    room = Room("TEST01", "host-user", "host")
    for i in range(1, players):
        room.add_player(f"user-{i}", f"player{i}")
    room.configure(room.host, category, target)
    return room


def ids(room):
    return list(room.players)  # host first


def types(messages):
    return [m["type"] for m in messages]


# ---------- rules (no networking) ----------

def test_how_many_can_score():
    assert [scorers_allowed(n) for n in range(2, 9)] == [1, 1, 2, 2, 3, 3, 4]


def test_only_the_host_starts_and_two_players_are_needed():
    room = make_room(players=1)
    with pytest.raises(RoomError, match="need_two_players"):
        room.start(room.host, now=0)
    room = make_room(players=2)
    with pytest.raises(RoomError, match="host_only"):
        room.start(ids(room)[1], now=0)
    with pytest.raises(RoomError, match="host_only"):
        room.configure(ids(room)[1], "mixed", 2000)


def test_first_right_answer_scores_and_ends_the_question():
    room = make_room()
    host, guest = ids(room)
    messages = room.start(host, now=100.0)
    question = next(m for m in messages if m["type"] == "question")
    assert question["mode"] == 1 and len(question["audio"]) > 1000
    assert "notes" not in str(room.snapshot())  # the answer is never in what browsers see before the reveal

    messages = room.answer(guest, 1, room.notes, now=101.0)  # 1 second: full speed bonus
    assert messages[0] == {"type": "correct", "player": guest, "rank": 1, "points": 150}
    assert "reveal" in types(messages)  # 2 players: only one can score, so the question ends
    assert room.players[guest].score == 150


def test_wrong_answer_costs_points_and_locks_you_out():
    room = make_room()
    host, guest = ids(room)
    room.start(host, now=0.0)
    messages = room.answer(host, 1, wrong_for(room), now=1.0)
    assert messages[0]["type"] == "wrong" and messages[0]["points"] == -50
    assert room.players[host].score == -50
    with pytest.raises(RoomError, match="already_answered"):
        room.answer(host, 1, room.notes, now=2.0)
    # the other player can still answer
    assert room.answer(guest, 1, room.notes, now=3.0)[0]["type"] == "correct"


def test_wrong_octave_locks_you_out_without_minus_points():
    room = make_room()
    host, _ = ids(room)
    room.start(host, now=0.0)
    note = room.notes[0]
    other_octave = note[:-1] + ("4" if note[-1] != "4" else "5")
    message = room.answer(host, 1, [other_octave], now=1.0)[0]
    assert message["type"] == "wrong" and message["octave"] is True and message["points"] == 0


def test_with_four_players_two_score_and_the_second_gets_less():
    room = make_room(players=4)
    host, p1, p2, p3 = ids(room)
    room.start(host, now=0.0)
    first = room.answer(p1, 1, room.notes, now=1.0)
    assert first[0]["points"] == 150 and "reveal" not in types(first)
    second = room.answer(p2, 1, room.notes, now=2.0)
    assert second[0] == {"type": "correct", "player": p2, "rank": 2, "points": 90}  # 150 × 0.6
    assert "reveal" in types(second)
    with pytest.raises(RoomError, match="not_now"):  # too late: the question is over
        room.answer(p3, 1, room.notes, now=3.0)


def test_time_limit_and_next_question():
    room = make_room()
    room.start(room.host, now=0.0)
    assert room.tick(now=5.0) == []
    assert "reveal" in types(room.tick(now=20.0))  # 1 note: 20 seconds to answer
    assert room.tick(now=21.0) == []  # showing the answer
    assert "question" in types(room.tick(now=24.0)) and room.round == 2


def test_game_ends_at_the_target_score():
    room = make_room(target=500)
    host, guest = ids(room)
    room.start(host, now=0.0)
    now = 0.0
    for _ in range(4):  # 150 points per question: 4 × 150 = 600
        messages = room.answer(guest, room.round, room.notes, now=now + 1)
        now += 10
        room.tick(now)
    finished = next(m for m in messages if m["type"] == "finished")
    assert [s["name"] for s in finished["standings"]] == ["player1", "host"]
    assert finished["standings"][0]["score"] == 600 and room.state == "finished"


def test_leaving_during_a_question():
    room = make_room()
    host, guest = ids(room)
    room.start(host, now=0.0)
    room.answer(host, 1, wrong_for(room), now=1.0)
    # the only player still able to answer leaves: the answer is shown
    assert "reveal" in types(room.disconnect(guest, now=2.0))
    # and they can come back during the game
    assert room.add_player("user-1", "player1").id == guest


# ---------- WebSocket: a real two-player game ----------

# Starlette's TestClient runs every WebSocket on its own event loop, unlike a real server,
# so these tests start a real uvicorn server in the background and connect like a browser.

@pytest.fixture
def live_server(client):
    """The app (with the test database and fake logins from conftest) on a real local server."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    while not server.started:
        time.sleep(0.05)
    yield f"ws://127.0.0.1:{port}"
    server.should_exit = True
    thread.join(timeout=5)


def receive_until(ws, kind):
    """Read messages until one of this type arrives (fails after 5 seconds instead of hanging)."""
    while True:
        message = json.loads(ws.recv(timeout=5))
        if message["type"] == kind:
            return message


def send(ws, message):
    ws.send(json.dumps(message))


def test_live_game_over_websockets(client, db, user, live_server):
    guest = CurrentUser(id=uuid.uuid4(), email="guest@example.com")
    client.patch("/api/me", json={"username": "host"})
    db.add(Profile(id=guest.id, username="guest"))
    db.commit()
    app.dependency_overrides[get_token_checker] = lambda: {"host-token": user, "guest-token": guest}.__getitem__

    code = client.post("/api/rooms").json()["code"]
    with connect(f"{live_server}/api/rooms/{code}/ws") as host_ws:
        send(host_ws, {"type": "auth", "token": "host-token"})
        receive_until(host_ws, "welcome")
        with connect(f"{live_server}/api/rooms/{code.lower()}/ws") as guest_ws:
            send(guest_ws, {"type": "auth", "token": "guest-token"})
            me = receive_until(guest_ws, "welcome")["you"]
            room = receive_until(host_ws, "room")
            while len(room["players"]) < 2:
                room = receive_until(host_ws, "room")

            send(host_ws, {"type": "configure", "category": "easy", "target": 500})
            send(guest_ws, {"type": "start"})  # not the host
            assert receive_until(guest_ws, "error")["error"] == "host_only"
            send(host_ws, {"type": "start"})
            question = receive_until(guest_ws, "question")
            assert question["mode"] == 1 and receive_until(host_ws, "question")["round"] == 1

            send(guest_ws, {"type": "answer", "round": 1, "notes": ROOMS[code].notes})
            correct = receive_until(host_ws, "correct")
            assert correct["player"] == me and correct["points"] > 0
            reveal = receive_until(host_ws, "reveal")
            assert reveal["notes"] == ROOMS[code].notes

            send(host_ws, {"type": "end"})
            standings = receive_until(guest_ws, "finished")["standings"]
            assert [s["name"] for s in standings] == ["guest", "host"]
    time.sleep(0.3)
    assert code not in ROOMS  # everyone left: the room is removed


def test_room_needs_a_username_and_a_real_code(client, live_server):
    assert client.post("/api/rooms").json()["detail"] == "username_required"
    with connect(f"{live_server}/api/rooms/NOPE00/ws") as ws:
        assert json.loads(ws.recv(timeout=5)) == {"type": "error", "error": "room_not_found"}
