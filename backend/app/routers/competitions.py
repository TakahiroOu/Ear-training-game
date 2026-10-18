"""Competitions: daily / weekly / monthly challenges and class competitions with a join code.

Cheating protection: the browser never receives a question's note names before answering.
It gets a mixed audio clip (app/audio.py), the server times the answer and grades it.
"""

import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import audio
from app.auth import CurrentUser, get_current_user, get_optional_user
from app.competitions import (
    ensure_current_competitions,
    is_active,
    new_class_seed,
    new_join_code,
    points_for,
    question,
    rank_of,
    utc_now,
)
from app.db import get_db
from app.models import Competition, CompetitionAnswer, CompetitionEntry, Profile
from app.music import NOTE_NAMES
from app.routers.sessions import get_or_create_profile
from app.scoring import classify

router = APIRouter(prefix="/api", tags=["competitions"])
LEADERBOARD_SIZE = 50


# ---------- shapes of the JSON ----------

class EntryOut(BaseModel):
    id: int
    competition_id: int
    question_count: int
    next_index: int
    next_mode: int | None  # how many notes the next question has (None when finished)
    score: int
    correct: int
    total_ms: int
    finished: bool
    rank: int | None


class CompetitionOut(BaseModel):
    id: int
    kind: str
    title: str | None
    question_count: int
    starts_at: datetime
    ends_at: datetime
    active: bool
    players: int
    join_code: str | None  # only shown to the person who created it
    my_entry: EntryOut | None


class ClassCompetitionIn(BaseModel):
    title: str = Field(min_length=1, max_length=60)
    question_count: int = Field(default=20, ge=4, le=40)
    days: int = Field(default=7, ge=1, le=30)


class CompetitionAnswerIn(BaseModel):
    index: int
    given_notes: list[str] = Field(min_length=1, max_length=len(NOTE_NAMES))


class CompetitionAnswerOut(BaseModel):
    result: str  # "right" | "octave" | "wrong"
    points: int
    question_notes: list[str]  # revealed only after answering
    entry: EntryOut


class LeaderboardRow(BaseModel):
    rank: int
    name: str
    score: int
    correct: int
    total_ms: int
    is_me: bool


class LeaderboardOut(BaseModel):
    competition: CompetitionOut
    rows: list[LeaderboardRow]
    me: LeaderboardRow | None  # your row, also when you're not in the top 50


# ---------- helpers ----------

def display_name(user_id: uuid.UUID, username: str | None):
    """Leaderboards never show emails: a chosen username, or 'Player-xxxx'."""
    return username or f"Player-{str(user_id)[:4]}"


def entry_out(db: Session, entry: CompetitionEntry):
    count = entry.competition.question_count
    finished = entry.finished_at is not None
    next_mode = None if finished else question(entry.competition, entry.next_index)[0]
    return EntryOut(
        id=entry.id, competition_id=entry.competition_id, question_count=count, next_index=entry.next_index,
        next_mode=next_mode, score=entry.score, correct=entry.correct, total_ms=entry.total_ms,
        finished=finished, rank=rank_of(db, entry),
    )


def competition_out(db: Session, competition: Competition, user: CurrentUser | None, now):
    players = db.scalar(
        select(func.count()).where(
            CompetitionEntry.competition_id == competition.id, CompetitionEntry.finished_at.is_not(None)
        )
    )
    entry = None
    if user:
        entry = db.scalar(
            select(CompetitionEntry).where(
                CompetitionEntry.competition_id == competition.id, CompetitionEntry.user_id == user.id
            )
        )
    return CompetitionOut(
        id=competition.id, kind=competition.kind, title=competition.title,
        question_count=competition.question_count, starts_at=competition.starts_at, ends_at=competition.ends_at,
        active=is_active(competition, now), players=players,
        join_code=competition.join_code if user and competition.created_by == user.id else None,
        my_entry=entry_out(db, entry) if entry else None,
    )


def my_entry(db: Session, entry_id: int, user: CurrentUser):
    entry = db.get(CompetitionEntry, entry_id)
    if entry is None or entry.user_id != user.id:  # someone else's entry looks the same as a missing one
        raise HTTPException(404, "Entry not found")
    return entry


# ---------- routes ----------

@router.get("/competitions", response_model=dict[str, list[CompetitionOut]])
def list_competitions(user: CurrentUser | None = Depends(get_optional_user), db: Session = Depends(get_db)):
    """This day's, week's and month's competitions, plus class competitions you created or joined."""
    now = utc_now()
    current = ensure_current_competitions(db, now)
    classes = []
    if user:
        joined = select(CompetitionEntry.competition_id).where(CompetitionEntry.user_id == user.id)
        classes = db.scalars(
            select(Competition)
            .where(Competition.kind == "class")
            .where((Competition.created_by == user.id) | Competition.id.in_(joined))
            .order_by(Competition.ends_at.desc())
            .limit(20)
        )
    return {
        "current": [competition_out(db, c, user, now) for c in current],
        "classes": [competition_out(db, c, user, now) for c in classes],
    }


@router.post("/competitions", status_code=201, response_model=CompetitionOut)
def create_class_competition(
    body: ClassCompetitionIn, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    """A competition for a class or a group of friends. Share the join code with them."""
    get_or_create_profile(db, user)
    now = utc_now()
    for _ in range(5):  # retry in the very unlikely case that the join code is taken
        competition = Competition(
            kind="class", title=body.title.strip(), seed=new_class_seed(), question_count=body.question_count,
            starts_at=now, ends_at=now + timedelta(days=body.days), join_code=new_join_code(), created_by=user.id,
        )
        db.add(competition)
        try:
            db.commit()
            break
        except IntegrityError:
            db.rollback()
    else:
        raise HTTPException(500, "Could not create a join code, please try again")
    db.refresh(competition)
    return competition_out(db, competition, user, now)


@router.get("/competitions/code/{join_code}", response_model=CompetitionOut)
def find_by_join_code(
    join_code: str, user: CurrentUser | None = Depends(get_optional_user), db: Session = Depends(get_db)
):
    competition = db.scalar(select(Competition).where(Competition.join_code == join_code.strip().upper()))
    if competition is None:
        raise HTTPException(404, "No competition with this code")
    return competition_out(db, competition, user, utc_now())


@router.get("/competitions/{competition_id}/leaderboard", response_model=LeaderboardOut)
def leaderboard(
    competition_id: int, user: CurrentUser | None = Depends(get_optional_user), db: Session = Depends(get_db)
):
    competition = db.get(Competition, competition_id)
    if competition is None:
        raise HTTPException(404, "Competition not found")

    finished = (
        select(CompetitionEntry, Profile.username)
        .join(Profile, Profile.id == CompetitionEntry.user_id)
        .where(CompetitionEntry.competition_id == competition_id, CompetitionEntry.finished_at.is_not(None))
        .order_by(CompetitionEntry.score.desc(), CompetitionEntry.total_ms, CompetitionEntry.finished_at)
    )

    def row(entry, username, rank):
        return LeaderboardRow(
            rank=rank, name=display_name(entry.user_id, username), score=entry.score, correct=entry.correct,
            total_ms=entry.total_ms, is_me=bool(user and entry.user_id == user.id),
        )

    rows = [row(entry, username, rank_of(db, entry)) for entry, username in db.execute(finished.limit(LEADERBOARD_SIZE))]
    me = next((r for r in rows if r.is_me), None)
    if user and me is None:
        mine = db.execute(finished.where(CompetitionEntry.user_id == user.id)).first()
        if mine:
            me = row(mine[0], mine[1], rank_of(db, mine[0]))
    return LeaderboardOut(competition=competition_out(db, competition, user, utc_now()), rows=rows, me=me)


@router.post("/competitions/{competition_id}/entries", response_model=EntryOut)
def enter(competition_id: int, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """Start (or continue) your one attempt at a competition."""
    competition = db.get(Competition, competition_id)
    if competition is None:
        raise HTTPException(404, "Competition not found")
    profile = get_or_create_profile(db, user)
    if not profile.username:
        raise HTTPException(409, "username_required")

    entry = db.scalar(
        select(CompetitionEntry).where(
            CompetitionEntry.competition_id == competition_id, CompetitionEntry.user_id == user.id
        )
    )
    if entry is None:
        if not is_active(competition, utc_now()):
            raise HTTPException(409, "This competition is not open")
        entry = CompetitionEntry(competition_id=competition_id, user_id=user.id)
        db.add(entry)
        db.commit()
        db.refresh(entry)
    return entry_out(db, entry)


@router.get("/entries/{entry_id}/audio")
def question_audio(entry_id: int, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """The current question as a WAV clip. The answer timer starts the first time it's fetched."""
    entry = my_entry(db, entry_id, user)
    if entry.finished_at is not None:
        raise HTTPException(409, "You have finished this competition")
    if entry.question_served_at is None:
        entry.question_served_at = utc_now()
        db.commit()
    _, notes = question(entry.competition, entry.next_index)
    return Response(audio.render(notes), media_type="audio/wav", headers={"Cache-Control": "no-store"})


@router.post("/entries/{entry_id}/answers", response_model=CompetitionAnswerOut)
def answer(
    entry_id: int,
    body: CompetitionAnswerIn,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entry = my_entry(db, entry_id, user)
    now = utc_now()
    if entry.finished_at is not None:
        raise HTTPException(409, "You have finished this competition")
    if not is_active(entry.competition, now):
        raise HTTPException(409, "This competition has ended")
    if body.index != entry.next_index:
        raise HTTPException(409, "Answer the questions in order")
    if entry.question_served_at is None:
        raise HTTPException(409, "Listen to the question first")
    unknown = [n for n in body.given_notes if n not in NOTE_NAMES]
    if unknown:
        raise HTTPException(422, f"unknown notes: {unknown}")

    mode, notes = question(entry.competition, entry.next_index)
    result = classify(body.given_notes, notes)
    points = points_for(result, mode)
    response_ms = int((now - entry.question_served_at).total_seconds() * 1000)

    db.add(CompetitionAnswer(
        entry_id=entry.id, index=entry.next_index, mode=mode, question_notes=notes,
        given_notes=body.given_notes, result=result, points=points, response_ms=response_ms,
    ))
    entry.score += points
    entry.correct += result == "right"
    entry.total_ms += response_ms
    entry.next_index += 1
    entry.question_served_at = None
    if entry.next_index >= entry.competition.question_count:
        entry.finished_at = now
    db.commit()
    db.refresh(entry)
    return CompetitionAnswerOut(result=result, points=points, question_notes=notes, entry=entry_out(db, entry))
