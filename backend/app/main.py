from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app import config
from app.music import make_question, parse_key
from app.routers import competitions, me, rooms, sessions, trainer

app = FastAPI(title="Ear Training API")
if config.FRONTEND_ORIGINS:
    # Browsers only let a website call an API on another address if the API allows it ("CORS")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.FRONTEND_ORIGINS,
        allow_methods=["*"],
        allow_headers=["*"],
    )
app.include_router(sessions.router)
app.include_router(me.router)
app.include_router(trainer.router)
app.include_router(competitions.router)
app.include_router(rooms.router)


@app.get("/api/health")
def health():
    """Lets the frontend (and you) check that the backend is running."""
    return {"status": "ok"}


@app.get("/api/questions")
def get_question(
    mode: int = Query(ge=1, le=4, description="How many notes to play (1-4)"),
    key: str | None = Query(default=None, description="Only use notes/chords of this key, e.g. D-major, F#-minor"),
):
    """Make a new question: the notes the player has to find on the piano."""
    if key:
        try:
            parse_key(key)
        except ValueError as error:
            raise HTTPException(422, str(error))
    return {"mode": mode, "key": key, "notes": make_question(mode, key)}
