"""Play-data analysis for everyone (anonymous totals) or for the logged-in player."""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.analytics import analyze
from app.auth import CurrentUser, get_optional_user
from app.db import get_db

router = APIRouter(prefix="/api", tags=["analytics"])


class ModeRow(BaseModel):
    mode: int
    answers: int
    players: int
    accuracy: float
    octave_rate: float
    median_ms: float | None


class NoteRow(BaseModel):
    note: str  # C, C#, ... B
    answers: int
    accuracy: float
    octave_rate: float


class IntervalRow(BaseModel):
    interval: str  # m2 ... P8, like the trainer
    semitones: int
    answers: int
    accuracy: float
    median_ms: float | None


class ChordRow(BaseModel):
    quality: str  # major, minor7, ... like the trainer
    answers: int
    accuracy: float
    median_ms: float | None


class ConfusionRow(BaseModel):
    played: str
    answered: str
    times: int


class AnalyticsOut(BaseModel):
    scope: str
    answers: int
    players: int | None  # only for everyone's data
    by_mode: list[ModeRow]
    notes: list[NoteRow]
    intervals: list[IntervalRow]
    chords: list[ChordRow]
    confusions: list[ConfusionRow]


@router.get("/analytics", response_model=AnalyticsOut)
def analytics(
    scope: Literal["everyone", "me"] = Query("everyone", description="'me' = only your answers (log in)"),
    user: CurrentUser | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """Which notes, intervals and chords are missed most, and what players hear instead.
    Everyone's data shows only totals, never who answered what."""
    if scope == "me" and user is None:
        raise HTTPException(401, "Log in to see your own analysis")
    return {"scope": scope, **analyze(db, user.id if scope == "me" else None)}
