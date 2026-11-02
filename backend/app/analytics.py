"""Play-data analysis: which notes, intervals and chords players miss most, and what they hear instead.

Everything is computed in PostgreSQL from the saved answers (Play mode + contests).
The queries share one set of CTEs (see BASE): note names are turned into numbers with a small
lookup table, so intervals and chord types can be worked out from the notes that were played.
"""

from sqlalchemy import text
from sqlalchemy.orm import Session

# Semitones -> interval key (the same keys as the trainer: m2 ... P8)
INTERVAL_KEYS = {1: "m2", 2: "M2", 3: "m3", 4: "M3", 5: "P4", 6: "TT", 7: "P5", 8: "m6", 9: "M6", 10: "m7",
                 11: "M7", 12: "P8"}

BASE = """
WITH
-- note letter -> pitch class (C = 0 ... B = 11); a note name is letter + octave, e.g. 'F#4'
pitch(name, pc) AS (
    VALUES ('C', 0), ('C#', 1), ('D', 2), ('D#', 3), ('E', 4), ('F', 5),
           ('F#', 6), ('G', 7), ('G#', 8), ('A', 9), ('A#', 10), ('B', 11)
),
-- chord types as semitones above the root (same names as the trainer)
chord_type(sort, quality, steps) AS (
    VALUES (1, 'major', ARRAY[0, 4, 7]), (2, 'minor', ARRAY[0, 3, 7]),
           (3, 'diminished', ARRAY[0, 3, 6]), (4, 'augmented', ARRAY[0, 4, 8]),
           (5, 'dominant7', ARRAY[0, 4, 7, 10]), (6, 'minor7', ARRAY[0, 3, 7, 10]),
           (7, 'major7', ARRAY[0, 4, 7, 11]), (8, 'half_diminished7', ARRAY[0, 3, 6, 10]),
           (9, 'diminished7', ARRAY[0, 3, 6, 9])
),
-- every saved answer: the Play mode and contests together
all_answers AS (
    SELECT 'play' AS source, a.id, s.user_id, a.mode, a.question_notes, a.given_notes, a.result, a.response_ms
    FROM answers a
    JOIN game_sessions s ON s.id = a.session_id
    UNION ALL
    SELECT 'contest', c.id, e.user_id, c.mode, c.question_notes, c.given_notes, c.result, c.response_ms
    FROM competition_answers c
    JOIN competition_entries e ON e.id = c.entry_id
),
-- everyone's answers, or one player's
scoped AS (
    SELECT * FROM all_answers
    WHERE CAST(:user_id AS uuid) IS NULL OR user_id = CAST(:user_id AS uuid)
),
-- one row per played note, as a number: pitch class and MIDI-like height (pc + 12 * octave)
played AS (
    SELECT s.source, s.id, p.pc, p.pc + 12 * CAST(right(x.note, 1) AS int) AS height
    FROM scoped s
    CROSS JOIN LATERAL unnest(s.question_notes) AS x(note)
    JOIN pitch p ON p.name = left(x.note, length(x.note) - 1)
)
"""

SUMMARY = BASE + """
SELECT mode,
       count(*) AS answers,
       count(DISTINCT user_id) AS players,
       avg(CAST(result = 'right' AS int)) AS accuracy,
       avg(CAST(result = 'octave' AS int)) AS octave_rate,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY response_ms) AS median_ms
FROM scoped
GROUP BY mode
ORDER BY mode
"""

# 1 note: accuracy for each note name (all octaves together)
NOTES = BASE + """
SELECT p.name AS note,
       count(*) AS answers,
       avg(CAST(s.result = 'right' AS int)) AS accuracy,
       avg(CAST(s.result = 'octave' AS int)) AS octave_rate
FROM scoped s
JOIN pitch p ON p.name = left(s.question_notes[1], length(s.question_notes[1]) - 1)
WHERE s.mode = 1
GROUP BY p.name, p.pc
ORDER BY p.pc
"""

# 2 notes: the distance between them, folded into one octave (a 10th counts as a 3rd; 12 = octave)
INTERVALS = BASE + """
SELECT (span - 1) % 12 + 1 AS semitones,
       count(*) AS answers,
       avg(CAST(s.result = 'right' AS int)) AS accuracy,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY s.response_ms) AS median_ms
FROM scoped s
JOIN (SELECT source, id, max(height) - min(height) AS span FROM played GROUP BY source, id) w
  ON w.source = s.source AND w.id = s.id
WHERE s.mode = 2 AND span > 0
GROUP BY 1
ORDER BY 1
"""

# 3-4 notes: try every played note as the root until the shape matches a known chord type
CHORDS = BASE + """
, shapes AS (
    SELECT DISTINCT ON (s.source, s.id) s.source, s.id, s.result, s.response_ms, t.sort, t.quality
    FROM scoped s
    JOIN played root ON root.source = s.source AND root.id = s.id
    CROSS JOIN LATERAL (
        SELECT array_agg(DISTINCT (n.pc - root.pc + 12) % 12 ORDER BY (n.pc - root.pc + 12) % 12) AS steps
        FROM played n
        WHERE n.source = s.source AND n.id = s.id
    ) shape
    JOIN chord_type t ON t.steps = shape.steps
    WHERE s.mode IN (3, 4)
    ORDER BY s.source, s.id
)
SELECT quality,
       count(*) AS answers,
       avg(CAST(result = 'right' AS int)) AS accuracy,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY response_ms) AS median_ms
FROM shapes
GROUP BY sort, quality
ORDER BY sort
"""

# 1 note answered with another note: what was heard instead (octave mistakes don't count here)
CONFUSIONS = BASE + """
SELECT q.name AS played,
       g.name AS answered,
       count(*) AS times
FROM scoped s
JOIN pitch q ON q.name = left(s.question_notes[1], length(s.question_notes[1]) - 1)
JOIN pitch g ON g.name = left(s.given_notes[1], length(s.given_notes[1]) - 1)
WHERE s.mode = 1 AND s.result = 'wrong' AND cardinality(s.given_notes) = 1
  AND q.pc <> g.pc  -- old answers marked a wrong octave as wrong
GROUP BY q.name, q.pc, g.name
ORDER BY times DESC, q.pc
LIMIT 10
"""


def _rows(db: Session, query, user_id):
    params = {"user_id": str(user_id) if user_id else None}
    return [dict(row._mapping) for row in db.execute(text(query), params)]


def analyze(db: Session, user_id=None):
    """Everyone's data (user_id=None) or one player's."""
    by_mode = _rows(db, SUMMARY, user_id)
    total = sum(r["answers"] for r in by_mode)
    players = None if user_id else _rows(db, BASE + "SELECT count(DISTINCT user_id) AS n FROM scoped", None)[0]["n"]
    return {
        "answers": total,
        "players": players,
        "by_mode": by_mode,
        "notes": _rows(db, NOTES, user_id),
        "intervals": [{**r, "interval": INTERVAL_KEYS[r["semitones"]]} for r in _rows(db, INTERVALS, user_id)],
        "chords": _rows(db, CHORDS, user_id),
        "confusions": _rows(db, CONFUSIONS, user_id),
    }
