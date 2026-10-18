"""Saving games for logged-in players. Guests play without calling these."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import CurrentUser, get_current_user
from app.db import get_db
from app.models import Answer, GameSession, Profile
from app.schemas import AnswerIn, AnswerResult, SessionOut
from app.scoring import MAX_MISTAKES, WIN_POINTS, classify, half_points_for, mistakes_for, points_for

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


def get_or_create_profile(db: Session, user: CurrentUser):
    """The first time a user saves something, create their profile row."""
    profile = db.get(Profile, user.id)
    if profile is None:
        profile = Profile(id=user.id)
        db.add(profile)
        db.flush()
    return profile


@router.post("", status_code=201, response_model=SessionOut)
def start_session(user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    get_or_create_profile(db, user)
    session = GameSession(user_id=user.id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.post("/{session_id}/answers", response_model=AnswerResult)
def save_answer(
    session_id: int,
    answer: AnswerIn,
    user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.get(GameSession, session_id)
    # Someone else's game looks the same as a missing one, so ids can't be guessed
    if session is None or session.user_id != user.id:
        raise HTTPException(404, "Game not found")
    if session.result is not None:
        raise HTTPException(409, "This game is already finished")
    if len(answer.question_notes) != answer.mode:
        raise HTTPException(422, "The number of question notes must match the mode")

    result = classify(answer.given_notes, answer.question_notes)
    if result == "right":
        session.points += points_for(answer.mode)
    elif result == "octave":
        session.points += half_points_for(answer.mode)  # and no mistake points
    else:
        session.mistakes += mistakes_for(answer.mode)

    if session.points >= WIN_POINTS or session.mistakes >= MAX_MISTAKES:
        session.result = "won" if session.points >= WIN_POINTS else "lost"
        session.ended_at = func.now()

    correct = result == "right"
    db.add(Answer(session_id=session.id, correct=correct, result=result, **answer.model_dump()))
    db.commit()
    db.refresh(session)
    return AnswerResult(correct=correct, result=result, session=session)
