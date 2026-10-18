"""Live rooms: play with friends at the same time.

Everyone hears the same question at the same moment. The first right answers score
(1 scorer with 2-3 players, half the players with 4 or more), faster answers score more.
A wrong answer costs points and locks you out of that question; the others keep trying.
The game ends when someone reaches the target score.

This file has no networking: every method gets the current time and returns the messages
to send, so the rules can be tested exactly. app/routers/rooms.py does the sending.
"""

import base64
import random
import secrets
from dataclasses import dataclass

from app import audio
from app.competitions import new_join_code, points_for, wrong_penalty
from app.music import make_question
from app.scoring import classify

TARGETS = [500, 1000, 2000, 3000]
MAX_PLAYERS = 8
RANK_MULTIPLIERS = [1.0, 0.6, 0.4, 0.3]  # 1st right answer, 2nd, 3rd, 4th
REVEAL_SECONDS = 4.0  # pause showing the answer before the next question
MAX_ROUNDS = 200  # safety net if nobody ever reaches the target


def question_seconds(mode):
    """Time to answer: 20 s for 1 note ... 35 s for 4 notes."""
    return 15 + 5 * mode


def scorers_allowed(player_count):
    """How many right answers score: 1 with 2-3 players, half the players with 4 or more."""
    return max(1, player_count // 2)


@dataclass
class Player:
    id: str  # public id sent to the browsers (not the account id)
    user_id: object
    name: str
    score: int = 0
    connected: bool = True


class RoomError(Exception):
    """Something a player isn't allowed to do right now (sent back to that player)."""


class Room:
    def __init__(self, code, host_user_id, host_name):
        self.code = code
        self.seed = f"room-{secrets.token_hex(8)}"
        self.category = "mixed"
        self.target = 1000
        self.state = "lobby"  # lobby | question | reveal | finished
        self.players: dict[str, Player] = {}
        self.host = self.add_player(host_user_id, host_name).id
        self.round = 0
        self.mode = 0
        self.notes: list[str] = []
        self.started_at = 0.0
        self.deadline = 0.0
        self.reveal_until = 0.0
        self.answered: set[str] = set()
        self.scorers: list[tuple[str, int]] = []  # (player id, points) in answer order

    # ---------- players ----------

    def connected_players(self):
        return [p for p in self.players.values() if p.connected]

    def add_player(self, user_id, name):
        """Join, or rejoin after losing the connection (same account = same player)."""
        for player in self.players.values():
            if player.user_id == user_id:
                player.connected = True
                player.name = name
                return player
        if self.state != "lobby":
            raise RoomError("game_running")
        if len(self.players) >= MAX_PLAYERS:
            raise RoomError("room_full")
        player = Player(id=secrets.token_hex(4), user_id=user_id, name=name)
        self.players[player.id] = player
        return player

    def disconnect(self, player_id, now):
        """A browser closed. In the lobby the player leaves; during a game they can come back."""
        player = self.players.get(player_id)
        if not player:
            return []
        if self.state == "lobby":
            del self.players[player_id]
        else:
            player.connected = False
        if self.host == player_id:
            remaining = self.connected_players()
            if remaining:
                self.host = remaining[0].id
        messages = [self.snapshot()]
        if self.state == "question" and self.everyone_answered():
            messages += self.reveal(now)
        return messages

    def is_empty(self):
        return not self.connected_players()

    # ---------- host actions ----------

    def require_host(self, player_id):
        if player_id != self.host:
            raise RoomError("host_only")

    def configure(self, player_id, category, target):
        self.require_host(player_id)
        if self.state != "lobby":
            raise RoomError("game_running")
        if category not in ("easy", "mixed") or target not in TARGETS:
            raise RoomError("bad_settings")
        self.category, self.target = category, target
        return [self.snapshot()]

    def start(self, player_id, now):
        self.require_host(player_id)
        if self.state not in ("lobby", "finished"):
            raise RoomError("game_running")
        if len(self.connected_players()) < 2:
            raise RoomError("need_two_players")
        # Players who left for good are removed, everyone starts from 0
        self.players = {pid: p for pid, p in self.players.items() if p.connected}
        for player in self.players.values():
            player.score = 0
        self.seed = f"room-{secrets.token_hex(8)}"
        self.round = 0
        return self.next_round(now)

    def end(self, player_id):
        self.require_host(player_id)
        if self.state in ("lobby", "finished"):
            raise RoomError("not_running")
        return self.finish()

    # ---------- the game ----------

    def next_round(self, now):
        if self.round >= MAX_ROUNDS:
            return self.finish()
        self.round += 1
        rng = random.Random(f"{self.seed}:{self.round}")
        self.mode = 1 if self.category == "easy" else rng.choice([1, 2, 3, 4])
        self.notes = make_question(self.mode, rng=rng)
        self.state = "question"
        self.started_at = now
        self.deadline = now + question_seconds(self.mode)
        self.answered = set()
        self.scorers = []
        clip = base64.b64encode(audio.render(self.notes)).decode()
        return [
            self.snapshot(),
            {
                "type": "question", "round": self.round, "mode": self.mode,
                "seconds": question_seconds(self.mode), "audio": clip,
            },
        ]

    def answer(self, player_id, round_number, given_notes, now):
        player = self.players.get(player_id)
        if self.state != "question" or round_number != self.round:
            raise RoomError("not_now")
        if player_id in self.answered:
            raise RoomError("already_answered")

        ms = int((now - self.started_at) * 1000)
        result = classify(given_notes, self.notes)
        self.answered.add(player_id)
        if result == "right":
            rank = len(self.scorers)
            points = round(points_for("right", self.mode, ms) * RANK_MULTIPLIERS[min(rank, 3)])
            player.score += points
            self.scorers.append((player_id, points))
            messages = [{"type": "correct", "player": player_id, "rank": rank + 1, "points": points}]
            if len(self.scorers) >= scorers_allowed(len(self.connected_players())):
                return messages + self.reveal(now)
        else:
            # Wrong: minus points. Wrong octave: locked out, but no minus points.
            points = wrong_penalty(self.mode) if result == "wrong" else 0
            player.score += points
            messages = [{"type": "wrong", "player": player_id, "points": points, "octave": result == "octave"}]
        messages.append(self.snapshot())
        if self.everyone_answered():
            messages += self.reveal(now)
        return messages

    def everyone_answered(self):
        return all(p.id in self.answered for p in self.connected_players())

    def reveal(self, now):
        """Show the answer and who scored. Ends the game if someone reached the target."""
        self.state = "reveal"
        self.reveal_until = now + REVEAL_SECONDS
        messages = [{
            "type": "reveal", "round": self.round, "notes": self.notes,
            "scorers": [{"player": pid, "points": points} for pid, points in self.scorers],
        }]
        if any(p.score >= self.target for p in self.players.values()):
            return messages + self.finish()
        return messages + [self.snapshot()]

    def finish(self):
        self.state = "finished"
        standings = sorted(self.players.values(), key=lambda p: -p.score)
        return [
            self.snapshot(),
            {"type": "finished", "standings": [{"player": p.id, "name": p.name, "score": p.score} for p in standings]},
        ]

    def tick(self, now):
        """Called a few times per second: time limits and the pause between questions."""
        if self.state == "question" and now >= self.deadline:
            return self.reveal(now)
        if self.state == "reveal" and now >= self.reveal_until:
            return self.next_round(now)
        return []

    def snapshot(self):
        """The room as everyone sees it (never includes the current answer)."""
        return {
            "type": "room", "code": self.code, "state": self.state, "host": self.host,
            "category": self.category, "target": self.target, "round": self.round,
            "scorers_allowed": scorers_allowed(len(self.connected_players())),
            "answered": sorted(self.answered),
            "players": [
                {"id": p.id, "name": p.name, "score": p.score, "connected": p.connected}
                for p in sorted(self.players.values(), key=lambda p: -p.score)
            ],
        }


# All rooms live in memory: fine for one server. (Several servers would need a shared store like Redis.)
ROOMS: dict[str, Room] = {}


def create_room(host_user_id, host_name):
    code = new_join_code()
    while code in ROOMS:
        code = new_join_code()
    room = Room(code, host_user_id, host_name)
    room.players[room.host].connected = False  # connected once their browser opens the room
    ROOMS[code] = room
    return room
