"""Game rules, same as frontend/src/game/rules.js.

The server calculates saved scores itself, so a player can't save fake points
by changing the browser code.
"""

WIN_POINTS = 50
MAX_MISTAKES = 50


def points_for(mode):
    return mode


def mistakes_for(mode):
    return 5 - mode


def is_correct(given_notes, question_notes):
    return sorted(given_notes) == sorted(question_notes)
