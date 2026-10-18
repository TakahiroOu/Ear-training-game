from fastapi import FastAPI, Query

from app.music import make_question
from app.routers import me, sessions

app = FastAPI(title="Ear Training API")
app.include_router(sessions.router)
app.include_router(me.router)


@app.get("/api/health")
def health():
    """Lets the frontend (and you) check that the backend is running."""
    return {"status": "ok"}


@app.get("/api/questions")
def get_question(mode: int = Query(ge=1, le=4, description="How many notes to play (1-4)")):
    """Make a new question: the notes the player has to find on the piano."""
    return {"mode": mode, "notes": make_question(mode)}
