import pytest

from app.music import NOTE_NAMES, TONICS, diatonic_chord, make_question, note_scale, parse_key
from app.scoring import classify, half_points_for

RUNS = 300
ALL_KEYS = [f"{tonic}-{quality}" for tonic in TONICS for quality in ("major", "minor")]


def pitch_classes(notes):
    return {NOTE_NAMES.index(n) % 12 for n in notes}


def test_parse_key():
    assert parse_key("D-major") == (2, "major")
    assert parse_key("F#-minor") == (6, "minor")
    for bad in ["H-major", "D-dorian", "d-major", "Db-major", ""]:
        with pytest.raises(ValueError):
            parse_key(bad)


def test_scales():
    # D major: D E F# G A B C#
    assert note_scale("D-major") == [2, 4, 6, 7, 9, 11, 1]
    # A harmonic minor: A B C D E F G#
    assert note_scale("A-minor") == [9, 11, 0, 2, 4, 5, 8]


def test_diatonic_triads_in_c_major():
    names = [[TONICS[pc] for pc in diatonic_chord("C-major", degree, 3)] for degree in range(7)]
    assert names == [
        ["C", "E", "G"], ["D", "F", "A"], ["E", "G", "B"], ["F", "A", "C"],
        ["G", "B", "D"], ["A", "C", "E"], ["B", "D", "F"],
    ]


def test_minor_key_uses_leading_tone_only_on_v_and_vii():
    a_minor = lambda degree, size: [TONICS[pc] for pc in diatonic_chord("A-minor", degree, size)]
    assert a_minor(0, 3) == ["A", "C", "E"]  # i is minor
    assert a_minor(2, 3) == ["C", "E", "G"]  # III is major (natural minor), not augmented
    assert a_minor(4, 3) == ["E", "G#", "B"]  # V is major
    assert a_minor(4, 4) == ["E", "G#", "B", "D"]  # V7 is a dominant 7th
    assert a_minor(6, 4) == ["G#", "B", "D", "F"]  # vii°7 is a diminished 7th


@pytest.mark.parametrize("key", ALL_KEYS)
def test_questions_stay_in_the_key(key):
    for mode in [1, 2]:
        for _ in range(RUNS // 10):
            notes = make_question(mode, key)
            assert len(notes) == mode
            assert pitch_classes(notes) <= set(note_scale(key))


@pytest.mark.parametrize("key", ["C-major", "F#-major", "A#-minor", "E-minor"])
def test_chords_are_from_the_key(key):
    triads = [set(diatonic_chord(key, d, 3)) for d in range(7)]
    sevenths = [set(diatonic_chord(key, d, 4)) for d in range(7)]
    for _ in range(RUNS):
        assert pitch_classes(make_question(3, key)) in triads
        assert pitch_classes(make_question(4, key)) in sevenths


def test_without_key_questions_work_as_before():
    for mode in [1, 2, 3, 4]:
        assert len(make_question(mode)) == mode


def test_classify():
    assert classify(["G4", "C4", "E4"], ["C4", "E4", "G4"]) == "right"
    assert classify(["C5", "E4", "G4"], ["C4", "E4", "G4"]) == "octave"
    assert classify(["C3"], ["C4"]) == "octave"
    assert classify(["C#4"], ["C4"]) == "wrong"
    assert classify(["C4", "E4"], ["C4", "E4", "G4"]) == "wrong"  # a note missing
    assert classify(["C4", "C5"], ["C4", "E4"]) == "wrong"


def test_half_points_round_down():
    assert [half_points_for(mode) for mode in [1, 2, 3, 4]] == [0, 1, 1, 2]


def test_question_api_with_key():
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    response = client.get("/api/questions?mode=3&key=G-major")
    assert response.status_code == 200
    assert response.json()["key"] == "G-major"
    assert client.get("/api/questions?mode=3&key=X-major").status_code == 422
