"""Ranked runs (anytime, Easy / Mixed, always 20 questions) and class competitions with a join code.

Cheating protection: the browser never receives a question's note names before answering.
It gets a mixed audio clip (app/audio.py), the server times the answer and grades it.
"""

import uuid
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import audio
from app.auth import CurrentUser, get_current_user, get_optional_user
from app.competitions import (
    ALWAYS_OPEN,
    RANKED_QUESTION_COUNT,
    best_entries,
    best_rank,
    ensure_ranked_competitions,
    is_active,
    new_join_code,
    new_seed,
    points_for,
    question,
    rank_of,
    utc_now,
    week_start,
)
from app.db import get_db
from app.models import Competition, CompetitionAnswer, CompetitionEntry, Profile
from app.music import NOTE_NAMES
from app.routers.sessions import get_or_create_profile
from app.scoring import classify

router = APIRouter(prefix="/api", tags=["competitions"])
LEADERBOARD_SIZE = 50
MAX_QUESTIONS = 100
Category = Literal["easy", "mixed"]
Period = Literal["all", "week"]


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
    rank: int | None  # None while playing (or for an old ranked run that wasn't 20 questions)


class BestOut(BaseModel):
    score: int
    question_count: int
    rank: int | None


class CompetitionOut(BaseModel):
    id: int
    kind: str  # "ranked" | "class"
    category: str  # "easy" | "mixed"
    title: str | None
    question_count: int
    active: bool  # class: False once the creator closed it
    players: int
    is_mine: bool  # you created it (you can close it)
    join_code: str | None  # only shown to the person who created it
    my_entry: EntryOut | None  # a run in progress (ranked) or your attempt (class)
    my_best: BestOut | None  # your best finished run and its rank


class ClassCompetitionIn(BaseModel):
    title: str = Field(min_length=1, max_length=60)
    category: Category = "mixed"
    question_count: int = Field(default=20, ge=1, le=MAX_QUESTIONS)


class CompetitionAnswerIn(BaseModel):
    index: int
    given_notes: list[str] = Field(min_length=1, max_length=len(NOTE_NAMES))


class CompetitionAnswerOut(BaseModel):
    result: str  # "right" | "octave" | "wrong"
    points: int  # can be negative for wrong answers
    response_ms: int
    question_notes: list[str]  # revealed only after answering
    entry: EntryOut


class LeaderboardRow(BaseModel):
    rank: int
    name: str
    score: int
    question_count: int
    correct: int
    total_ms: int
    is_me: bool


class LeaderboardOut(BaseModel):
    competition: CompetitionOut
    period: str
    rows: list[LeaderboardRow]
    me: LeaderboardRow | None  # your row, also when you're not in the top 50


# ---------- helpers ----------

def display_name(user_id: uuid.UUID, username: str | None):
    """Leaderboards never show emails: a chosen username, or 'Player-xxxx'."""
    return username or f"Player-{str(user_id)[:4]}"


def entry_rank(db: Session, entry: CompetitionEntry):
    if entry.finished_at is None:
        return None
    # Ranked: where this run would place among everyone's best runs
    return best_rank(db, entry) if entry.competition.kind == "ranked" else rank_of(db, entry)


def current_question(entry: CompetitionEntry):
    return question(entry.seed, entry.next_index, entry.question_count, entry.competition.category)


def entry_out(db: Session, entry: CompetitionEntry):
    finished = entry.finished_at is not None
    return EntryOut(
        id=entry.id, competition_id=entry.competition_id, question_count=entry.question_count,
        next_index=entry.next_index, next_mode=None if finished else current_question(entry)[0],
        score=entry.score, correct=entry.correct, total_ms=entry.total_ms, finished=finished,
        rank=entry_rank(db, entry),
    )


def my_entries(competition_id, user_id):
    return select(CompetitionEntry).where(
        CompetitionEntry.competition_id == competition_id, CompetitionEntry.user_id == user_id
    )


def best_out(db: Session, entry):
    return BestOut(
        score=entry.score, question_count=entry.question_count, rank=entry_rank(db, entry),
    )


def competition_out(db: Session, competition: Competition, user: CurrentUser | None, now):
    ranked = competition.kind == "ranked"
    finished = (CompetitionEntry.competition_id == competition.id) & CompetitionEntry.finished_at.is_not(None)
    if ranked:
        finished &= CompetitionEntry.question_count == RANKED_QUESTION_COUNT
    players = db.scalar(select(func.count(func.distinct(CompetitionEntry.user_id))).where(finished))

    open_entry = best = None
    if user:
        open_entry = db.scalar(my_entries(competition.id, user.id).where(CompetitionEntry.finished_at.is_(None)))
        done = my_entries(competition.id, user.id).where(CompetitionEntry.finished_at.is_not(None))
        if ranked:
            done = done.where(CompetitionEntry.question_count == RANKED_QUESTION_COUNT)
        done = done.order_by(CompetitionEntry.score.desc(), CompetitionEntry.total_ms)
        best_entry = db.scalar(done)
        if best_entry:
            best = best_out(db, best_entry)
            if not ranked and open_entry is None:
                open_entry = best_entry  # class: your one attempt
    mine = bool(user and competition.created_by == user.id)
    return CompetitionOut(
        id=competition.id, kind=competition.kind, category=competition.category, title=competition.title,
        question_count=competition.question_count, active=is_active(competition, now), players=players,
        is_mine=mine, join_code=competition.join_code if mine else None,
        my_entry=entry_out(db, open_entry) if open_entry else None, my_best=best,
    )


def my_entry(db: Session, entry_id: int, user: CurrentUser):
    entry = db.get(CompetitionEntry, entry_id)
    if entry is None or entry.user_id != user.id:  # someone else's entry looks the same as a missing one
        raise HTTPException(404, "Entry not found")
    return entry


# ---------- routes ----------

@router.get("/competitions", response_model=dict[str, list[CompetitionOut]])
def list_competitions(user: CurrentUser | None = Depends(get_optional_user), db: Session = Depends(get_db)):
    """The ranked competitions (Easy, Mixed), plus class competitions you created or joined."""
    now = utc_now()
    ranked = ensure_ranked_competitions(db)
    classes = []
    if user:
        joined = select(CompetitionEntry.competition_id).where(CompetitionEntry.user_id == user.id)
        classes = db.scalars(
            select(Competition)
            .where(Competition.kind == "class")
            .where((Competition.created_by == user.id) | Competition.id.in_(joined))
            .order_by(Competition.created_at.desc())
            .limit(20)
        )
    return {
        "ranked": [competition_out(db, c, user, now) for c in ranked],
        "classes": [competition_out(db, c, user, now) for c in classes],
    }


@router.post("/competitions", status_code=201, response_model=CompetitionOut)
def create_class_competition(
    body: ClassCompetitionIn, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    """A competition for a class or a group of friends. It stays open until you close it."""
    get_or_create_profile(db, user)
    now = utc_now()
    for _ in range(5):  # retry in the very unlikely case that the join code is taken
        competition = Competition(
            kind="class", category=body.category, title=body.title.strip(), seed=new_seed("class"),
            question_count=body.question_count, starts_at=now, ends_at=ALWAYS_OPEN[1],
            join_code=new_join_code(), created_by=user.id,
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


@router.post("/competitions/{competition_id}/close", response_model=CompetitionOut)
def close_class_competition(
    competition_id: int, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Only the creator can close it. The leaderboard stays visible; nobody can start anymore."""
    competition = db.get(Competition, competition_id)
    if competition is None or competition.kind != "class" or competition.created_by != user.id:
        raise HTTPException(404, "Competition not found")
    now = utc_now()
    competition.ends_at = min(competition.ends_at, now)
    db.commit()
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
    competition_id: int,
    period: Period = Query("all", description="Ranked only: 'week' = best runs since Monday (Japan time)"),
    user: CurrentUser | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    competition = db.get(Competition, competition_id)
    if competition is None:
        raise HTTPException(404, "Competition not found")
    now = utc_now()

    if competition.kind == "ranked":
        source = best_entries(competition_id, week_start(now) if period == "week" else None)
    else:
        source = (
            select(CompetitionEntry)
            .where(CompetitionEntry.competition_id == competition_id, CompetitionEntry.finished_at.is_not(None))
            .subquery()
        )
    order = (source.c.score.desc(), source.c.total_ms)  # everyone played the same number of questions
    # rank() gives the same rank to exactly equal results
    ranked = (
        select(source, Profile.username, func.rank().over(order_by=order).label("rank"))
        .join(Profile, Profile.id == source.c.user_id)
        .order_by("rank")
    )

    def row(r):
        return LeaderboardRow(
            rank=r.rank, name=display_name(r.user_id, r.username), score=r.score, question_count=r.question_count,
            correct=r.correct, total_ms=r.total_ms,
            is_me=bool(user and r.user_id == user.id),
        )

    rows = [row(r) for r in db.execute(ranked.limit(LEADERBOARD_SIZE))]
    me = next((r for r in rows if r.is_me), None)
    if user and me is None:
        everyone = ranked.subquery()
        mine = db.execute(select(everyone).where(everyone.c.user_id == user.id)).first()
        if mine:
            me = row(mine)
    return LeaderboardOut(
        competition=competition_out(db, competition, user, now), period=period, rows=rows, me=me
    )


@router.post("/competitions/{competition_id}/entries", response_model=EntryOut)
def enter(
    competition_id: int,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Ranked: continue your unfinished run, or start a new 20-question run with new questions.
    Class: start (or continue) your one attempt."""
    competition = db.get(Competition, competition_id)
    if competition is None:
        raise HTTPException(404, "Competition not found")
    profile = get_or_create_profile(db, user)
    if not profile.username:
        raise HTTPException(409, "username_required")

    unfinished = db.scalar(my_entries(competition_id, user.id).where(CompetitionEntry.finished_at.is_(None)))
    if unfinished:
        return entry_out(db, unfinished)
    if competition.kind == "class" and db.scalar(my_entries(competition_id, user.id)):
        raise HTTPException(409, "You have already played this competition")
    if not is_active(competition, utc_now()):
        raise HTTPException(409, "This competition is not open")

    ranked = competition.kind == "ranked"
    entry = CompetitionEntry(
        competition_id=competition_id, user_id=user.id,
        seed=new_seed(competition.seed) if ranked else competition.seed,
        question_count=RANKED_QUESTION_COUNT if ranked else competition.question_count,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry_out(db, entry)


@router.get("/entries/{entry_id}/audio")
def question_audio(entry_id: int, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """The current question as a WAV clip. The answer timer starts the first time it's fetched."""
    entry = my_entry(db, entry_id, user)
    if entry.finished_at is not None:
        raise HTTPException(409, "You have finished this run")
    if entry.question_served_at is None:
        entry.question_served_at = utc_now()
        db.commit()
    _, notes = current_question(entry)
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
        raise HTTPException(409, "You have finished this run")
    if not is_active(entry.competition, now):
        raise HTTPException(409, "This competition has ended")
    if body.index != entry.next_index:
        raise HTTPException(409, "Answer the questions in order")
    if entry.question_served_at is None:
        raise HTTPException(409, "Listen to the question first")
    unknown = [n for n in body.given_notes if n not in NOTE_NAMES]
    if unknown:
        raise HTTPException(422, f"unknown notes: {unknown}")

    mode, notes = current_question(entry)
    result = classify(body.given_notes, notes)
    response_ms = int((now - entry.question_served_at).total_seconds() * 1000)
    points = points_for(result, mode, response_ms)

    db.add(CompetitionAnswer(
        entry_id=entry.id, index=entry.next_index, mode=mode, question_notes=notes,
        given_notes=body.given_notes, result=result, points=points, response_ms=response_ms,
    ))
    entry.score += points
    entry.correct += result == "right"
    entry.total_ms += response_ms
    entry.next_index += 1
    entry.question_served_at = None
    if entry.next_index >= entry.question_count:
        entry.finished_at = now
    db.commit()
    db.refresh(entry)
    return CompetitionAnswerOut(
        result=result, points=points, response_ms=response_ms, question_notes=notes, entry=entry_out(db, entry)
    )
