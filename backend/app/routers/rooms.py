"""Live rooms over WebSockets (a connection that stays open, so the server can push to everyone at once).

Browser → server messages (JSON):
    {"type": "auth", "token": "..."}                       first message: who you are
    {"type": "configure", "category": "easy", "target": 1000}   host, in the lobby
    {"type": "start"}  /  {"type": "end"}                  host
    {"type": "answer", "round": 3, "notes": ["C4", "E4"]}
Server → browser messages: see app/rooms.py ("room", "question", "correct", "wrong", "reveal", "finished"),
plus {"type": "welcome", "you": "<your player id>"} and {"type": "error", "error": "..."}.
"""

import asyncio
import time

import jwt
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.auth import CurrentUser, get_current_user, get_token_checker
from app.db import get_db
from app.models import Profile
from app.rooms import ROOMS, Room, RoomError, create_room

router = APIRouter(prefix="/api/rooms", tags=["rooms"])

# Open connections per room: {room code: {player id: websocket}}
CONNECTIONS: dict[str, dict[str, WebSocket]] = {}
TICKERS: dict[str, asyncio.Task] = {}
TICK_SECONDS = 0.2


def username_of(db: Session, user: CurrentUser):
    profile = db.get(Profile, user.id)
    if not profile or not profile.username:
        raise HTTPException(409, "username_required")
    return profile.username


@router.post("", status_code=201)
def new_room(user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create a room. Share its code with friends; everyone opens the room to join."""
    room = create_room(user.id, username_of(db, user))
    return {"code": room.code}


async def send_all(room: Room, messages):
    for message in messages:
        for socket in list(CONNECTIONS.get(room.code, {}).values()):
            try:
                await socket.send_json(message)
            except Exception:
                pass  # that browser is gone; its own handler cleans up


async def run_ticker(room: Room):
    """Checks time limits a few times per second while anyone is in the room."""
    while room.code in ROOMS:
        await send_all(room, room.tick(time.monotonic()))
        await asyncio.sleep(TICK_SECONDS)


@router.websocket("/{code}/ws")
async def room_socket(
    websocket: WebSocket,
    code: str,
    check_token=Depends(get_token_checker),
    db: Session = Depends(get_db),
):
    await websocket.accept()
    room = ROOMS.get(code.upper())
    if room is None:
        await websocket.send_json({"type": "error", "error": "room_not_found"})
        await websocket.close()
        return

    # The first message must say who you are
    try:
        hello = await websocket.receive_json()
        user = check_token(hello.get("token", ""))
        name = username_of(db, user)
        player = room.add_player(user.id, name)
    except (jwt.PyJWTError, HTTPException, RoomError, ValueError, KeyError) as error:
        reason = error.args[0] if isinstance(error, RoomError) else getattr(error, "detail", "not_logged_in")
        await websocket.send_json({"type": "error", "error": reason})
        await websocket.close()
        return

    CONNECTIONS.setdefault(room.code, {})[player.id] = websocket
    await websocket.send_json({"type": "welcome", "you": player.id})
    await send_all(room, [room.snapshot()])
    if room.code not in TICKERS or TICKERS[room.code].done():
        TICKERS[room.code] = asyncio.create_task(run_ticker(room))

    try:
        while True:
            message = await websocket.receive_json()
            now = time.monotonic()
            try:
                kind = message.get("type")
                if kind == "configure":
                    replies = room.configure(player.id, message.get("category"), message.get("target"))
                elif kind == "start":
                    replies = room.start(player.id, now)
                elif kind == "end":
                    replies = room.end(player.id)
                elif kind == "answer":
                    replies = room.answer(player.id, message.get("round"), list(message.get("notes", [])), now)
                else:
                    raise RoomError("unknown_message")
                await send_all(room, replies)
            except RoomError as error:
                await websocket.send_json({"type": "error", "error": error.args[0]})
    except WebSocketDisconnect:
        pass
    finally:
        CONNECTIONS.get(room.code, {}).pop(player.id, None)
        await send_all(room, room.disconnect(player.id, time.monotonic()))
        if room.is_empty():
            ROOMS.pop(room.code, None)
            CONNECTIONS.pop(room.code, None)
            ticker = TICKERS.pop(room.code, None)
            if ticker:
                ticker.cancel()
