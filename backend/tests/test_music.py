from app.music import (
    NOTE_NAMES,
    make_1note,
    make_2notes,
    make_3notes,
    make_4notes,
    make_question,
)

# Random questions: run each check many times so every random branch gets tested.
RUNS = 500


def pitch_classes(notes):
    """Note letters without octave, as numbers 0-11 relative to C (e.g. "E4" -> 4)."""
    return [NOTE_NAMES.index(n) % 12 for n in notes]


def is_chord(notes, shape):
    """True if the notes form the given chord shape (e.g. [0, 4, 7]) on the first note."""
    root = pitch_classes(notes)[0]
    return sorted(pitch_classes(notes)) == sorted((root + step) % 12 for step in shape)


def test_note_names_cover_three_octaves():
    assert len(NOTE_NAMES) == 36
    assert NOTE_NAMES[0] == "C3" and NOTE_NAMES[-1] == "B5"


def test_every_mode_returns_that_many_valid_notes():
    for mode in [1, 2, 3, 4]:
        for _ in range(RUNS):
            notes = make_question(mode)
            assert len(notes) == mode
            assert all(n in NOTE_NAMES for n in notes)
            assert len(set(notes)) == mode  # no note is repeated


def test_one_note_is_in_range():
    for _ in range(RUNS):
        assert make_1note()[0] in NOTE_NAMES


def test_two_notes_are_never_next_to_each_other():
    for _ in range(RUNS):
        note1, note2 = make_2notes()
        assert abs(NOTE_NAMES.index(note1) - NOTE_NAMES.index(note2)) > 1


def test_three_notes_are_a_major_or_minor_triad():
    for _ in range(RUNS):
        notes = make_3notes()
        assert is_chord(notes, [0, 4, 7]) or is_chord(notes, [0, 3, 7])


def test_four_notes_are_a_dominant_or_minor_seventh():
    for _ in range(RUNS):
        notes = make_4notes()
        assert is_chord(notes, [0, 4, 7, 10]) or is_chord(notes, [0, 3, 7, 10])
