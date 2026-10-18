"""Music logic for the ear-training questions.

Ported from AudioCreator in legacy/main.py. pygame is gone: the server only works with
note *names* (like "C#4"). The browser loads the sound files and plays them.

Notes are numbered by their position in NOTE_NAMES (0 = C3 ... 35 = B5).
A note's "pitch class" is its letter without the octave, as a number 0-11 (C=0, C#=1 ... B=11).
"""

import re
from random import choice

NOTE_NAMES = [
    "C3", "C#3", "D3", "D#3", "E3", "F3", "F#3", "G3", "G#3", "A3", "A#3", "B3",
    "C4", "C#4", "D4", "D#4", "E4", "F4", "F#4", "G4", "G#4", "A4", "A#4", "B4",
    "C5", "C#5", "D5", "D#5", "E5", "F5", "F#5", "G5", "G#5", "A5", "A#5", "B5",
]
TONICS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Root notes are picked from the middle octave (C4..B4), like the original game.
MIDDLE_OCTAVE = range(12, 24)

# Steps above the tonic, in semitones
MAJOR_SCALE = [0, 2, 4, 5, 7, 9, 11]
NATURAL_MINOR_SCALE = [0, 2, 3, 5, 7, 8, 10]
HARMONIC_MINOR_SCALE = [0, 2, 3, 5, 7, 8, 11]  # raised 7th (leading tone), as in exam dictation


def pitch_class(index):
    return index % 12


def make_octave(index):
    """Keep the note, or move it one octave up or down (wrapping around C3..B5)."""
    return (index + choice([0, 12, -12])) % len(NOTE_NAMES)


def to_names(indexes):
    return [NOTE_NAMES[i] for i in indexes]


# ---------- keys (調性) ----------

KEY_PATTERN = re.compile(r"^(?P<tonic>[A-G]#?)-(?P<quality>major|minor)$")


def parse_key(key):
    """'D-major' -> (2, 'major'),  'F#-minor' -> (6, 'minor'). Raises ValueError for unknown keys."""
    match = KEY_PATTERN.match(key or "")
    if not match or match["tonic"] not in TONICS:
        raise ValueError(f"unknown key: {key!r} (use e.g. 'C-major' or 'F#-minor')")
    return TONICS.index(match["tonic"]), match["quality"]


def note_scale(key):
    """Pitch classes used for single notes: major scale, or harmonic minor."""
    tonic, quality = parse_key(key)
    steps = MAJOR_SCALE if quality == "major" else HARMONIC_MINOR_SCALE
    return [(tonic + step) % 12 for step in steps]


def diatonic_chord(key, degree, size):
    """Pitch classes of the chord built in thirds on a scale degree (0 = I ... 6 = VII).

    size 3 = triad, 4 = seventh chord. In minor, chords on V and VII use the raised 7th
    (so V is major and VII is diminished, as in classical harmony); the others use natural minor.
    """
    tonic, quality = parse_key(key)
    if quality == "major":
        steps = MAJOR_SCALE
    else:
        steps = HARMONIC_MINOR_SCALE if degree in (4, 6) else NATURAL_MINOR_SCALE
    return [(tonic + steps[(degree + 2 * i) % 7]) % 12 for i in range(size)]


def notes_in(pitch_classes, indexes):
    return [i for i in indexes if pitch_class(i) in pitch_classes]


def build_chord(root_pitch_class, chord_pitch_classes):
    """Root in the middle octave, the other notes stacked above it, then each note's octave randomized."""
    root = next(i for i in MIDDLE_OCTAVE if pitch_class(i) == root_pitch_class)
    intervals = [(pc - root_pitch_class) % 12 for pc in chord_pitch_classes]
    return [make_octave(root + interval) for interval in intervals]


# ---------- questions ----------

def make_1note(key=None):
    pool = notes_in(note_scale(key), MIDDLE_OCTAVE) if key else MIDDLE_OCTAVE
    return to_names([make_octave(choice(pool))])


def make_2notes(key=None):
    """Two random notes that are never the same or right next to each other."""
    pool = notes_in(note_scale(key), MIDDLE_OCTAVE) if key else MIDDLE_OCTAVE
    while True:
        note1 = make_octave(choice(pool))
        note2 = make_octave(choice(pool))
        if abs(note1 - note2) > 1:
            return to_names([note1, note2])


def make_3notes(key=None):
    """No key: a minor or major triad on a random root. With a key: a triad from that key."""
    if key:
        chord = diatonic_chord(key, choice(range(7)), 3)
        return to_names(build_chord(chord[0], chord))
    root = choice(MIDDLE_OCTAVE)
    third = choice([3, 4])  # minor (root, +3, +7) or major (root, +4, +7)
    return to_names([make_octave(root), make_octave(root + third), make_octave(root + 7)])


def make_4notes(key=None):
    """No key: a dominant 7th or minor 7th chord. With a key: a seventh chord from that key."""
    if key:
        chord = diatonic_chord(key, choice(range(7)), 4)
        return to_names(build_chord(chord[0], chord))
    root = choice(MIDDLE_OCTAVE)
    third = choice([3, 4])  # minor 7th (root, +3, +7, +10) or dominant 7th (root, +4, +7, +10)
    return to_names([
        make_octave(root),
        make_octave(root + third),
        make_octave(root + 7),
        make_octave(root + 10),
    ])


QUESTION_MAKERS = {1: make_1note, 2: make_2notes, 3: make_3notes, 4: make_4notes}


def make_question(mode, key=None):
    if key:
        parse_key(key)  # fail early with a clear message for unknown keys
    return QUESTION_MAKERS[mode](key)
