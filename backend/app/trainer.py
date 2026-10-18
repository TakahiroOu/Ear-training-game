"""Interval & chord trainer: hear notes, answer with the *name* (短3度, 長三和音, ...).

All shapes are written as semitones above the lowest note of the root position.
"""

from random import choice

from app.music import NOTE_NAMES, TONICS

INTERVALS = {
    "m2": 1, "M2": 2, "m3": 3, "M3": 4, "P4": 5, "TT": 6,
    "P5": 7, "m6": 8, "M6": 9, "m7": 10, "M7": 11, "P8": 12,
}
TRIADS = {
    "major": [0, 4, 7],
    "minor": [0, 3, 7],
    "diminished": [0, 3, 6],
    "augmented": [0, 4, 8],
}
SEVENTHS = {
    "dominant7": [0, 4, 7, 10],
    "minor7": [0, 3, 7, 10],
    "major7": [0, 4, 7, 11],
    "half_diminished7": [0, 3, 6, 10],  # 減五短七
    "diminished7": [0, 3, 6, 9],
}
INVERSIONS = [0, 1, 2, 3]  # root position, 1st, 2nd, 3rd (3rd only exists for seventh chords)


class RangeTooSmall(ValueError):
    pass


def invert(shape, inversion):
    """Move the lowest `inversion` notes up an octave: [0, 4, 7] 1st inversion -> [4, 7, 12]."""
    return shape[inversion:] + [step + 12 for step in shape[:inversion]]


def place(steps, low, high):
    """Put a shape (semitones above its lowest note) at a random height inside low..high."""
    span = steps[-1] - steps[0]
    starts = [i for i in range(low, high + 1) if i + span <= high]
    if not starts:
        raise RangeTooSmall("The range is too small for the chosen intervals/chords")
    start = choice(starts)
    return [start + step - steps[0] for step in steps]


def make_trainer_question(intervals, triads, sevenths, inversions, low, high):
    """Returns {"notes": [...lowest to highest], "answer": {...}}.

    Each chosen item (an interval or a chord type) is equally likely.
    """
    low_index, high_index = NOTE_NAMES.index(low), NOTE_NAMES.index(high)
    items = [("interval", name) for name in intervals]
    items += [("chord", name) for name in triads + sevenths]
    if not items:
        raise ValueError("Choose at least one interval or chord")

    # Only keep items that can actually fit in the range
    def fits(item):
        kind, name = item
        if kind == "interval":
            return INTERVALS[name] <= high_index - low_index
        shape = TRIADS.get(name) or SEVENTHS[name]
        return any(
            inv < len(shape) and invert(shape, inv)[-1] - invert(shape, inv)[0] <= high_index - low_index
            for inv in inversions
        )

    items = [item for item in items if fits(item)]
    if not items:
        raise RangeTooSmall("The range is too small for the chosen intervals/chords")

    kind, name = choice(items)
    if kind == "interval":
        notes = place([0, INTERVALS[name]], low_index, high_index)
        return {
            "notes": [NOTE_NAMES[i] for i in notes],
            "answer": {"kind": "interval", "name": name, "inversion": None, "root": None},
        }

    shape = TRIADS.get(name) or SEVENTHS[name]
    possible = [
        inv for inv in inversions
        if inv < len(shape) and invert(shape, inv)[-1] - invert(shape, inv)[0] <= high_index - low_index
    ]
    inversion = choice(possible)
    steps = invert(shape, inversion)
    notes = place(steps, low_index, high_index)
    root_index = notes[0] - steps[0]  # where the root would be in root position
    return {
        "notes": [NOTE_NAMES[i] for i in notes],
        "answer": {"kind": "chord", "name": name, "inversion": inversion, "root": TONICS[root_index % 12]},
    }
