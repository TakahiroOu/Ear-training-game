"""Shapes of the JSON the API receives and sends. FastAPI checks incoming data against these
and rejects anything wrong with a clear error (status 422)."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.music import NOTE_NAMES


class AnswerIn(BaseModel):
    mode: int = Field(ge=1, le=4)
    question_notes: list[str]
    given_notes: list[str] = Field(max_length=len(NOTE_NAMES))
    response_ms: int | None = Field(default=None, ge=0)

    @field_validator("question_notes", "given_notes")
    @classmethod
    def notes_must_exist(cls, notes):
        unknown = [n for n in notes if n not in NOTE_NAMES]
        if unknown:
            raise ValueError(f"unknown notes: {unknown}")
        return notes


class SessionOut(BaseModel):
    id: int
    points: int
    mistakes: int
    result: str | None
    started_at: datetime
    ended_at: datetime | None

    model_config = {"from_attributes": True}


class AnswerResult(BaseModel):
    correct: bool
    session: SessionOut


class ProfileOut(BaseModel):
    id: str
    username: str | None
    email: str | None


class ModeStats(BaseModel):
    mode: int
    answered: int
    correct: int


class MissedNote(BaseModel):
    note: str
    missed: int


class StatsOut(BaseModel):
    games_played: int
    wins: int
    losses: int
    by_mode: list[ModeStats]
    most_missed_notes: list[MissedNote]
    recent_sessions: list[SessionOut]
