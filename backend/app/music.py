"""Music logic for the ear-training questions.

Ported from AudioCreator in legacy/main.py. pygame is gone: the server only works with
note *names* (like "C#4"). The browser loads the sound files and plays them.
"""

from random import choice

NOTE_NAMES = [
    "C3", "C#3", "D3", "D#3", "E3", "F3", "F#3", "G3", "G#3", "A3", "A#3", "B3",
    "C4", "C#4", "D4", "D#4", "E4", "F4", "F#4", "G4", "G#4", "A4", "A#4", "B4",
    "C5", "C#5", "D5", "D#5", "E5", "F5", "F#5", "G5", "G#5", "A5", "A#5", "B5",
]

# Root notes are picked from the middle octave (C4..B4), like the original game.
MIDDLE_OCTAVE = range(12, 24)


def make_octave(index):
    """Keep the note, or move it one octave up or down (wrapping around C3..B5)."""
    return (index + choice([0, 12, -12])) % len(NOTE_NAMES)


def to_names(indexes):
    return [NOTE_NAMES[i] for i in indexes]


def make_1note():
    return to_names([make_octave(choice(MIDDLE_OCTAVE))])


def make_2notes():
    """Two random notes that are never the same or right next to each other."""
    while True:
        note1 = make_octave(choice(MIDDLE_OCTAVE))
        note2 = make_octave(choice(MIDDLE_OCTAVE))
        if abs(note1 - note2) > 1:
            return to_names([note1, note2])


def make_3notes():
    """A minor (root, +3, +7) or major (root, +4, +7) triad, each note in a random octave."""
    root = choice(MIDDLE_OCTAVE)
    third = choice([3, 4])
    return to_names([make_octave(root), make_octave(root + third), make_octave(root + 7)])


def make_4notes():
    """A dominant 7th (root, +4, +7, +10) or minor 7th (root, +3, +7, +10) chord."""
    root = choice(MIDDLE_OCTAVE)
    third = choice([3, 4])
    return to_names([
        make_octave(root),
        make_octave(root + third),
        make_octave(root + 7),
        make_octave(root + 10),
    ])


QUESTION_MAKERS = {1: make_1note, 2: make_2notes, 3: make_3notes, 4: make_4notes}


def make_question(mode):
    return QUESTION_MAKERS[mode]()
