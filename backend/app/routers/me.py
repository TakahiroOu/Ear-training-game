"""Information about the logged-in player: profile and statistics."""

from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.auth import CurrentUser, get_current_user
from app.db import get_db
from app.models import Answer, GameSession, Profile, TrainerResult
from app.schemas import MissedNote, ModeStats, ProfileOut, StatsOut

router = APIRouter(prefix="/api/me", tags=["me"])


@router.get("", response_model=ProfileOut)
def get_me(user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.get(Profile, user.id)
    return ProfileOut(id=str(user.id), username=profile.username if profile else None, email=user.email)


@router.get("/stats", response_model=StatsOut)
def get_stats(user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    sessions = select(GameSession).where(GameSession.user_id == user.id)

    # Games played / won / lost, counted by the database in one query:
    #   SELECT count(*), count(*) FILTER (result = 'won'), ... FROM game_sessions WHERE user_id = ...
    games_played, wins, losses = db.execute(
        select(
            func.count(),
            func.count(case((GameSession.result == "won", 1))),
            func.count(case((GameSession.result == "lost", 1))),
        ).where(GameSession.user_id == user.id)
    ).one()

    # Accuracy per mode:  SELECT mode, count(*), count(correct), count(octave) ... GROUP BY mode
    my_answers = select(Answer).join(GameSession).where(GameSession.user_id == user.id)
    by_mode = db.execute(
        select(
            Answer.mode,
            func.count(),
            func.count(case((Answer.correct, 1))),
            func.count(case((Answer.result == "octave", 1))),
        )
        .join(GameSession)
        .where(GameSession.user_id == user.id)
        .group_by(Answer.mode)
        .order_by(Answer.mode)
    ).all()

    # Which notes were played but not found, over all wrong answers
    missed = Counter()
    for answer in db.scalars(my_answers.where(Answer.correct.is_(False))):
        missed.update(set(answer.question_notes) - set(answer.given_notes))

    recent = db.scalars(sessions.order_by(GameSession.started_at.desc(), GameSession.id.desc()).limit(10))

    trainer_tests = db.scalars(
        select(TrainerResult)
        .where(TrainerResult.user_id == user.id)
        .order_by(TrainerResult.created_at.desc(), TrainerResult.id.desc())
        .limit(10)
    )

    return StatsOut(
        games_played=games_played,
        wins=wins,
        losses=losses,
        by_mode=[ModeStats(mode=m, answered=a, correct=c, octave=o) for m, a, c, o in by_mode],
        most_missed_notes=[MissedNote(note=n, missed=c) for n, c in missed.most_common(5)],
        recent_sessions=list(recent),
        trainer_tests=list(trainer_tests),
    )
