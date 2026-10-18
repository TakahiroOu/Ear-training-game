"""Game rules, same as frontend/src/game/rules.js.

The server calculates saved scores itself, so a player can't save fake points
by changing the browser code.
"""

from app.music import NOTE_NAMES, pitch_class

WIN_POINTS = 50
MAX_MISTAKES = 50


def points_for(mode):
    return mode


def half_points_for(mode):
    """Right notes in the wrong octave: half the points, rounded down."""
    return mode // 2


def mistakes_for(mode):
    return 5 - mode


def classify(given_notes, question_notes):
    """'right'  - exactly the notes that were played (any order)
    'octave' - the right note letters, but at least one in the wrong octave
    'wrong'  - anything else
    """
    if sorted(given_notes) == sorted(question_notes):
        return "right"

    def letters(notes):
        return sorted(pitch_class(NOTE_NAMES.index(n)) for n in notes)

    if letters(given_notes) == letters(question_notes):
        return "octave"
    return "wrong"
