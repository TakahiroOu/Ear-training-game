"""The database tables. Each class is one table, each attribute one column.

Changing a table? Also add a migration in alembic/versions/ (see README).
"""

import uuid
from datetime import datetime

from sqlalchemy import ARRAY, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Profile(Base):
    """One row per player. The id is the user's id in Supabase Auth,
    which stores the email and password, so we never handle passwords."""

    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    username: Mapped[str | None] = mapped_column(String(40), unique=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class GameSession(Base):
    """One game, from Start until someone reaches 50 points or 50 mistakes."""

    __tablename__ = "game_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("profiles.id", ondelete="CASCADE"), index=True)
    points: Mapped[int] = mapped_column(default=0)
    mistakes: Mapped[int] = mapped_column(default=0)
    result: Mapped[str | None] = mapped_column(String(10))  # None while playing, then "won" or "lost"
    started_at: Mapped[datetime] = mapped_column(server_default=func.now())
    ended_at: Mapped[datetime | None]

    answers: Mapped[list["Answer"]] = relationship(back_populates="session")


class Answer(Base):
    """One checked question: what was played and what the player chose."""

    __tablename__ = "answers"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("game_sessions.id", ondelete="CASCADE"), index=True)
    mode: Mapped[int]  # how many notes were played (1-4)
    question_notes: Mapped[list[str]] = mapped_column(ARRAY(String(4)))
    given_notes: Mapped[list[str]] = mapped_column(ARRAY(String(4)))
    correct: Mapped[bool]
    result: Mapped[str] = mapped_column(String(10))  # "right" | "octave" (right letters, wrong octave) | "wrong"
    key: Mapped[str | None] = mapped_column(String(10))  # e.g. "D-major", or None when any note could be played
    response_ms: Mapped[int | None]  # time from hearing the question to checking
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    session: Mapped[GameSession] = relationship(back_populates="answers")
