"""The database tables. Each class is one table, each attribute one column.

Changing a table? Also add a migration in alembic/versions/ (see README).
"""

import uuid
from datetime import datetime

from sqlalchemy import ARRAY, JSON, ForeignKey, String, UniqueConstraint, func
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


class TrainerResult(Base):
    """One finished test in the interval & chord trainer."""

    __tablename__ = "trainer_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("profiles.id", ondelete="CASCADE"), index=True)
    total: Mapped[int]
    correct: Mapped[int]
    settings: Mapped[dict] = mapped_column(JSON)  # which intervals/chords/voicings/range were tested
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Competition(Base):
    """A contest.

    kind "ranked": always open, play as often as you like; every run gets its own seed (new questions),
                   every finished run is a leaderboard row, under the name typed for it.
    kind "class":  created by a player, joined with `join_code`, one attempt each, same questions for all.
    category: "easy" (all questions 1 note) or "mixed" (1 → 4 notes). Times are stored in UTC.
    """

    __tablename__ = "competitions"

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(10))
    category: Mapped[str] = mapped_column(String(10), default="mixed")
    title: Mapped[str | None] = mapped_column(String(60))  # only for class competitions
    seed: Mapped[str] = mapped_column(String(40), unique=True)
    question_count: Mapped[int]  # class competitions (ranked runs choose their own)
    starts_at: Mapped[datetime]
    ends_at: Mapped[datetime]  # class: far in the future until the creator closes it
    join_code: Mapped[str | None] = mapped_column(String(8), unique=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("profiles.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class CompetitionEntry(Base):
    """One run / attempt at a competition (ranked: many per player, class: one per player)."""

    __tablename__ = "competition_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    competition_id: Mapped[int] = mapped_column(ForeignKey("competitions.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("profiles.id", ondelete="CASCADE"), index=True)
    player_name: Mapped[str | None] = mapped_column(String(20))  # the leaderboard name typed for this run
    seed: Mapped[str] = mapped_column(String(40))  # ranked: new for every run; class: the competition's seed
    question_count: Mapped[int]  # ranked: always 20; class: the competition's
    next_index: Mapped[int] = mapped_column(default=0)  # the question the player is on
    question_served_at: Mapped[datetime | None]  # when the current question's audio was first sent
    score: Mapped[int] = mapped_column(default=0)
    correct: Mapped[int] = mapped_column(default=0)
    total_ms: Mapped[int] = mapped_column(default=0)  # answering time, used to break ties
    started_at: Mapped[datetime] = mapped_column(server_default=func.now())
    finished_at: Mapped[datetime | None]

    competition: Mapped[Competition] = relationship()


class CompetitionAnswer(Base):
    __tablename__ = "competition_answers"
    __table_args__ = (UniqueConstraint("entry_id", "index"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    entry_id: Mapped[int] = mapped_column(ForeignKey("competition_entries.id", ondelete="CASCADE"), index=True)
    index: Mapped[int]
    mode: Mapped[int]
    question_notes: Mapped[list[str]] = mapped_column(ARRAY(String(4)))
    given_notes: Mapped[list[str]] = mapped_column(ARRAY(String(4)))
    result: Mapped[str] = mapped_column(String(10))
    points: Mapped[int]
    response_ms: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
