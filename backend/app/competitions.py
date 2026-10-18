"""Competition rules: periods, questions (the same for everyone), scoring and ranking."""

import random
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import Competition, CompetitionEntry
from app.music import make_question

JST = timezone(timedelta(hours=9))  # Japan has no daylight saving time
QUESTION_COUNTS = {"daily": 20, "weekly": 30, "monthly": 40}
JOIN_CODE_LETTERS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no 0/O or 1/I, which look alike


def utc_now():
    """Now in UTC, without timezone info (that's how the database stores times)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def to_utc(moment):
    return moment.astimezone(timezone.utc).replace(tzinfo=None)


def current_periods(now):
    """The daily / weekly / monthly competitions running at `now` (UTC). Periods start at midnight JST."""
    today = now.replace(tzinfo=timezone.utc).astimezone(JST).replace(hour=0, minute=0, second=0, microsecond=0)
    week = today - timedelta(days=today.weekday())  # Monday
    month = today.replace(day=1)
    next_month = (month + timedelta(days=32)).replace(day=1)
    return [
        ("daily", f"daily-{today:%Y-%m-%d}", today, today + timedelta(days=1)),
        ("weekly", f"weekly-{week:%Y-%m-%d}", week, week + timedelta(days=7)),
        ("monthly", f"monthly-{month:%Y-%m}", month, next_month),
    ]


def ensure_current_competitions(db: Session, now):
    """Create this day's / week's / month's competitions if they don't exist yet."""
    for kind, seed, starts, ends in current_periods(now):
        db.execute(
            insert(Competition)
            .values(
                kind=kind, seed=seed, question_count=QUESTION_COUNTS[kind],
                starts_at=to_utc(starts), ends_at=to_utc(ends),
            )
            .on_conflict_do_nothing(index_elements=["seed"])  # two requests at once can't create it twice
        )
    db.commit()
    seeds = [seed for _, seed, _, _ in current_periods(now)]
    return list(db.scalars(select(Competition).where(Competition.seed.in_(seeds)).order_by(Competition.ends_at)))


def new_class_seed():
    return f"class-{secrets.token_hex(8)}"


def new_join_code():
    return "".join(secrets.choice(JOIN_CODE_LETTERS) for _ in range(6))


def mode_for(index, question_count):
    """Questions get harder: the first quarter has 1 note, the last quarter 4 notes."""
    return 1 + index * 4 // question_count


def question(competition, index):
    """(mode, notes) of question `index`. The same seed always gives the same question."""
    rng = random.Random(f"{competition.seed}:{index}")
    mode = mode_for(index, competition.question_count)
    return mode, make_question(mode, rng=rng)


def points_for(result, mode):
    return {"right": 100 * mode, "octave": 50 * mode}.get(result, 0)


def is_active(competition, now):
    return competition.starts_at <= now < competition.ends_at


def better_than(entry):
    """SQL condition: finished entries ranked above `entry` (higher score, or same score but faster)."""
    return and_(
        CompetitionEntry.competition_id == entry.competition_id,
        CompetitionEntry.finished_at.is_not(None),
        or_(
            CompetitionEntry.score > entry.score,
            and_(CompetitionEntry.score == entry.score, CompetitionEntry.total_ms < entry.total_ms),
        ),
    )


def rank_of(db: Session, entry):
    if entry.finished_at is None:
        return None
    return db.scalar(select(func.count()).where(better_than(entry))) + 1
