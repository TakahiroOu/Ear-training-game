"""Interval & chord trainer: questions for everyone, saved test results for logged-in players."""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.orm import Session

from app.auth import CurrentUser, get_current_user
from app.db import get_db
from app.models import TrainerResult
from app.music import NOTE_NAMES
from app.routers.sessions import get_or_create_profile
from app.trainer import INTERVALS, SEVENTHS, TRIADS, RangeTooSmall, make_trainer_question

router = APIRouter(prefix="/api/trainer", tags=["trainer"])

IntervalName = Literal[tuple(INTERVALS)]
TriadName = Literal[tuple(TRIADS)]
SeventhName = Literal[tuple(SEVENTHS)]
NoteName = Literal[tuple(NOTE_NAMES)]


class TrainerSettings(BaseModel):
    intervals: list[IntervalName] = []
    triads: list[TriadName] = []
    sevenths: list[SeventhName] = []
    inversions: list[Literal[0, 1, 2, 3]] = [0]
    low: NoteName = "C3"
    high: NoteName = "B4"

    @model_validator(mode="after")
    def check(self):
        if NOTE_NAMES.index(self.low) >= NOTE_NAMES.index(self.high):
            raise ValueError("The lowest note must be below the highest note")
        if not self.inversions:
            raise ValueError("Choose at least one voicing")
        return self


class TrainerResultIn(BaseModel):
    total: int = Field(ge=1, le=200)
    correct: int = Field(ge=0)
    settings: TrainerSettings

    @model_validator(mode="after")
    def correct_not_above_total(self):
        if self.correct > self.total:
            raise ValueError("correct can't be more than total")
        return self


@router.post("/question")
def trainer_question(settings: TrainerSettings):
    try:
        return make_trainer_question(**settings.model_dump())
    except (ValueError, RangeTooSmall) as error:
        raise HTTPException(422, str(error))


@router.post("/results", status_code=201)
def save_trainer_result(
    result: TrainerResultIn,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Save a finished test (practice mode isn't saved)."""
    get_or_create_profile(db, user)
    row = TrainerResult(
        user_id=user.id, total=result.total, correct=result.correct, settings=result.settings.model_dump()
    )
    db.add(row)
    db.commit()
    return {"id": row.id}
