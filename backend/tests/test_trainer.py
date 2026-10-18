import pytest

from app.music import NOTE_NAMES, TONICS
from app.trainer import INTERVALS, SEVENTHS, TRIADS, RangeTooSmall, invert, make_trainer_question

RUNS = 300
ALL = {
    "intervals": list(INTERVALS),
    "triads": list(TRIADS),
    "sevenths": list(SEVENTHS),
    "inversions": [0, 1, 2, 3],
    "low": "C3",
    "high": "B5",
}


def steps(notes):
    """Semitones above the lowest note: ["E4", "G4", "C5"] -> [0, 3, 8]"""
    indexes = [NOTE_NAMES.index(n) for n in notes]
    return [i - indexes[0] for i in indexes]


def test_invert():
    assert invert([0, 4, 7], 0) == [0, 4, 7]
    assert invert([0, 4, 7], 1) == [4, 7, 12]
    assert invert([0, 4, 7], 2) == [7, 12, 16]
    assert invert([0, 4, 7, 10], 3) == [10, 12, 16, 19]


def test_answers_match_the_notes():
    for _ in range(RUNS):
        question = make_trainer_question(**ALL)
        notes, answer = question["notes"], question["answer"]
        assert notes == sorted(notes, key=NOTE_NAMES.index)  # lowest to highest
        if answer["kind"] == "interval":
            assert steps(notes) == [0, INTERVALS[answer["name"]]]
        else:
            shape = TRIADS.get(answer["name"]) or SEVENTHS[answer["name"]]
            expected = invert(shape, answer["inversion"])
            assert steps(notes) == [s - expected[0] for s in expected]
            # The root is the note that started the root position
            root_note = notes[(len(shape) - answer["inversion"]) % len(shape)]
            assert TONICS.index(answer["root"]) == NOTE_NAMES.index(root_note) % 12


def test_stays_in_range_and_only_uses_chosen_items():
    settings = {**ALL, "intervals": ["P5"], "triads": ["minor"], "sevenths": [], "low": "E3", "high": "E4"}
    for _ in range(RUNS):
        question = make_trainer_question(**settings)
        assert question["answer"]["name"] in {"P5", "minor"}
        assert all(NOTE_NAMES.index("E3") <= NOTE_NAMES.index(n) <= NOTE_NAMES.index("E4") for n in question["notes"])


def test_third_inversion_only_for_sevenths():
    settings = {**ALL, "intervals": [], "triads": ["major"], "sevenths": [], "inversions": [3]}
    with pytest.raises(RangeTooSmall):  # a triad has no 3rd inversion, so nothing fits
        make_trainer_question(**settings)


def test_range_too_small():
    with pytest.raises(RangeTooSmall):
        make_trainer_question(**{**ALL, "intervals": ["P8"], "triads": [], "sevenths": [], "low": "C4", "high": "G4"})


def test_trainer_api(client):
    response = client.post("/api/trainer/question", json={"triads": ["major"], "low": "C3", "high": "B4"})
    assert response.status_code == 200
    assert response.json()["answer"]["name"] == "major"

    assert client.post("/api/trainer/question", json={}).status_code == 422  # nothing chosen
    assert client.post("/api/trainer/question", json={"intervals": ["P5"], "low": "C5", "high": "C4"}).status_code == 422
    assert client.post("/api/trainer/question", json={"intervals": ["P9"]}).status_code == 422


RESULT = {"total": 20, "correct": 17, "settings": {"intervals": ["m3", "M3"]}}


def test_guests_cannot_save_test_results(guest_client):
    assert guest_client.post("/api/trainer/results", json=RESULT).status_code == 401


def test_save_test_results_and_see_them_in_stats(client):
    body = RESULT
    assert client.post("/api/trainer/results", json=body).status_code == 201
    assert client.post("/api/trainer/results", json={**body, "correct": 21}).status_code == 422

    tests = client.get("/api/me/stats").json()["trainer_tests"]
    assert [(t["total"], t["correct"]) for t in tests] == [(20, 17)]
