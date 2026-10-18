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

def half_life_ms(mode):
    """How fast the speed bonus shrinks: 2 s for 1 note, 3.5 s for 2, 5 s for 3, 6.5 s for 4.
    One note shrinks fastest; chords give more time to think."""
    return int((2.0 + 1.5 * (mode - 1)) * 1000)


def speed_factor(mode, ms):
    """×1.5 at the very start, shrinking smoothly toward ×0.25: every split second counts.
    After one half-life the part above ×0.25 has halved (×0.875), after two ×0.56, and so on."""
    return 0.25 + 1.25 * 0.5 ** (ms / half_life_ms(mode))


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


# Ranked runs can have any length, so they're compared by AVERAGE points per question
# (then average time). Very short runs don't count, so one lucky question can't win.
MIN_RANKED_QUESTIONS = 10
AVERAGE = (CompetitionEntry.score * 1.0 / CompetitionEntry.question_count).label("average")
AVERAGE_MS = (CompetitionEntry.total_ms * 1.0 / CompetitionEntry.question_count).label("average_ms")


def counts_for_ranking(entry):
    return entry.finished_at is not None and entry.question_count >= MIN_RANKED_QUESTIONS


def best_entries(competition_id, since=None):
    """Ranked competitions: each player's best finished run (highest average, then fastest)."""
    query = (
        select(CompetitionEntry, AVERAGE, AVERAGE_MS)
        .where(
            CompetitionEntry.competition_id == competition_id,
            CompetitionEntry.finished_at.is_not(None),
            CompetitionEntry.question_count >= MIN_RANKED_QUESTIONS,
        )
        .distinct(CompetitionEntry.user_id)
        .order_by(CompetitionEntry.user_id, AVERAGE.desc(), AVERAGE_MS)
    )
    if since is not None:
        query = query.where(CompetitionEntry.finished_at >= since)
    return query.subquery()


def best_rank(db: Session, entry, since=None):
    """Where a run places among everyone's best runs (None if it's too short to count)."""
    if not counts_for_ranking(entry):
        return None
    average = entry.score / entry.question_count
    average_ms = entry.total_ms / entry.question_count
    best = best_entries(entry.competition_id, since)
    better = select(func.count()).select_from(best).where(
        or_(best.c.average > average, and_(best.c.average == average, best.c.average_ms < average_ms))
    )
    return db.scalar(better) + 1
