"""Competition rules: categories, questions (the same for everyone with the same seed), speed scoring, ranking."""

import random
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import Competition, CompetitionEntry
from app.music import make_question

JST = timezone(timedelta(hours=9))  # Japan has no daylight saving time
CATEGORIES = ["easy", "mixed"]  # easy: every question is 1 note. mixed: 1 → 4 notes, harder toward the end
RANKED_QUESTION_COUNT = 20
JOIN_CODE_LETTERS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no 0/O or 1/I, which look alike
ALWAYS_OPEN = (datetime(2020, 1, 1), datetime(9999, 12, 31))


def utc_now():
    """Now in UTC, without timezone info (that's how the database stores times)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def week_start(now):
    """Monday 00:00 Japan time of the week containing `now` (UTC), returned in UTC."""
    local = now.replace(tzinfo=timezone.utc).astimezone(JST)
    monday = (local - timedelta(days=local.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    return monday.astimezone(timezone.utc).replace(tzinfo=None)


def ensure_ranked_competitions(db: Session):
    """The two always-open ranked competitions (created the first time they're needed)."""
    for category in CATEGORIES:
        db.execute(
            insert(Competition)
            .values(
                kind="ranked", category=category, seed=f"ranked-{category}",
                question_count=RANKED_QUESTION_COUNT, starts_at=ALWAYS_OPEN[0], ends_at=ALWAYS_OPEN[1],
            )
            .on_conflict_do_nothing(index_elements=["seed"])  # two requests at once can't create it twice
        )
    db.commit()
    seeds = [f"ranked-{category}" for category in CATEGORIES]
    return list(db.scalars(select(Competition).where(Competition.seed.in_(seeds)).order_by(Competition.id)))


def new_seed(prefix):
    return f"{prefix}-{secrets.token_hex(8)}"


def new_join_code():
    return "".join(secrets.choice(JOIN_CODE_LETTERS) for _ in range(6))


def mode_for(index, question_count, category):
    """How many notes question `index` has. Mixed: the first quarter 1 note ... the last quarter 4 notes."""
    if category == "easy":
        return 1
    return 1 + index * 4 // question_count


def question(seed, index, question_count, category):
    """(mode, notes) of question `index`. The same seed always gives the same question."""
    rng = random.Random(f"{seed}:{index}")
    mode = mode_for(index, question_count, category)
    return mode, make_question(mode, rng=rng)


# ---------- speed scoring ----------

def fast_ms(mode):
    """Answer within this time for the full speed bonus: 3.5 s for 1 note ... 8 s for 4 notes."""
    return int((2.0 + 1.5 * mode) * 1000)


def speed_factor(mode, ms):
    """×1.5 when fast, falling steadily to ×0.5 at three times the fast time, ×0.25 when slower than that."""
    fast = fast_ms(mode)
    slow = fast * 3
    if ms <= fast:
        return 1.5
    if ms >= slow:
        return 0.25
    return 1.5 - (ms - fast) / (slow - fast)


def wrong_penalty(mode):
    """A wrong answer costs points: -50 for 1 note ... -200 for 4 notes."""
    return -50 * mode


def points_for(result, mode, ms):
    """Right: 100 × notes × speed. Wrong octave: half of that. Wrong: minus points.
    Because the base grows with the number of notes, speed matters more on harder questions."""
    base = 100 * mode * speed_factor(mode, ms)
    if result == "right":
        return round(base)
    if result == "octave":
        return round(base / 2)
    return wrong_penalty(mode)


# ---------- ranking ----------

def is_active(competition, now):
    return competition.starts_at <= now < competition.ends_at


def better_than(entry):
    """SQL condition: finished entries of the same competition ranked above `entry`."""
    return and_(
        CompetitionEntry.competition_id == entry.competition_id,
        CompetitionEntry.finished_at.is_not(None),
        or_(
            CompetitionEntry.score > entry.score,
            and_(CompetitionEntry.score == entry.score, CompetitionEntry.total_ms < entry.total_ms),
        ),
    )


def rank_of(db: Session, entry):
    """Class competitions: one entry per player, so rank among entries."""
    if entry.finished_at is None:
        return None
    return db.scalar(select(func.count()).where(better_than(entry))) + 1


def best_entries(competition_id, since=None):
    """Ranked competitions: each player's best finished run (highest score, then fastest)."""
    query = (
        select(CompetitionEntry)
        .where(CompetitionEntry.competition_id == competition_id, CompetitionEntry.finished_at.is_not(None))
        .distinct(CompetitionEntry.user_id)
        .order_by(CompetitionEntry.user_id, CompetitionEntry.score.desc(), CompetitionEntry.total_ms)
    )
    if since is not None:
        query = query.where(CompetitionEntry.finished_at >= since)
    return query.subquery()


def best_rank(db: Session, entry, since=None):
    """Rank of a player's best run among everyone's best runs."""
    best = best_entries(entry.competition_id, since)
    better = select(func.count()).select_from(best).where(
        or_(best.c.score > entry.score, and_(best.c.score == entry.score, best.c.total_ms < entry.total_ms))
    )
    return db.scalar(better) + 1
