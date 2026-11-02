import uuid
from datetime import datetime

from app.models import Answer, Competition, CompetitionAnswer, CompetitionEntry, GameSession, Profile


def add_answers(db, user_id, rows):
    """rows: (mode, question_notes, given_notes, result, response_ms) saved as one Play game."""
    if db.get(Profile, user_id) is None:
        db.add(Profile(id=user_id))
        db.flush()
    session = GameSession(user_id=user_id)
    db.add(session)
    db.flush()
    for mode, question, given, result, ms in rows:
        db.add(Answer(session_id=session.id, mode=mode, question_notes=question, given_notes=given,
                      correct=result == "right", result=result, response_ms=ms))
    db.commit()


def by(rows, key):
    return {row[key]: row for row in rows}


def test_intervals_notes_chords_and_confusions(client, db, user):
    add_answers(db, user.id, [
        # 1 note: A is heard as G# twice, C right once, E in the wrong octave once
        (1, ["A4"], ["G#4"], "wrong", 1000),
        (1, ["A3"], ["G#3"], "wrong", 1200),
        (1, ["C4"], ["C4"], "right", 800),
        (1, ["E4"], ["E3"], "octave", 900),
        # 2 notes: minor 2nd missed, major 3rd right, a 10th counts as a 3rd, an octave
        (2, ["E4", "F4"], ["E4", "F#4"], "wrong", 3000),
        (2, ["C3", "E3"], ["C3", "E3"], "right", 2000),
        (2, ["C3", "E4"], ["C3", "E4"], "right", 2500),
        (2, ["G3", "G4"], ["G3", "G4"], "right", 1500),
        # chords in any order and octave: C major (2nd inversion), A minor, G7, B half-diminished
        (3, ["G3", "C4", "E5"], ["G3", "C4", "E5"], "right", 4000),
        (3, ["E4", "A3", "C5"], ["E4", "A3", "C4"], "octave", 5000),
        (4, ["B3", "F4", "D5", "G3"], ["B3", "F4", "D5", "G3"], "right", 6000),
        (4, ["B3", "D4", "F4", "A4"], ["B3", "D4", "F4", "G4"], "wrong", 7000),
    ])
    data = client.get("/api/analytics").json()
    assert data["answers"] == 12 and data["players"] == 1

    notes = by(data["notes"], "note")
    assert notes["A"]["answers"] == 2 and notes["A"]["accuracy"] == 0
    assert notes["C"]["accuracy"] == 1 and notes["E"]["octave_rate"] == 1

    intervals = by(data["intervals"], "interval")
    assert intervals["m2"]["accuracy"] == 0 and intervals["m2"]["semitones"] == 1
    assert intervals["M3"]["answers"] == 2 and intervals["M3"]["accuracy"] == 1  # C3-E3 and C3-E4
    assert intervals["P8"]["semitones"] == 12

    chords = by(data["chords"], "quality")
    assert set(chords) == {"major", "minor", "dominant7", "half_diminished7"}
    assert chords["major"]["accuracy"] == 1 and chords["minor"]["accuracy"] == 0
    assert [c["quality"] for c in data["chords"]] == ["major", "minor", "dominant7", "half_diminished7"]

    assert data["confusions"] == [{"played": "A", "answered": "G#", "times": 2}]  # octave mistakes don't count

    one_note = by(data["by_mode"], "mode")[1]
    assert one_note["answers"] == 4 and one_note["accuracy"] == 0.25 and one_note["median_ms"] == 950


def test_contest_answers_count_and_me_shows_only_mine(client, db, user):
    add_answers(db, user.id, [(1, ["D4"], ["D4"], "right", 700)])
    other = uuid.uuid4()
    add_answers(db, other, [(1, ["D4"], ["C4"], "wrong", 900)])
    competition = Competition(kind="ranked", category="easy", seed="s", question_count=20,
                              starts_at=datetime(2020, 1, 1), ends_at=datetime(9999, 1, 1))
    db.add(competition)
    db.flush()
    entry = CompetitionEntry(competition_id=competition.id, user_id=other, seed="e", question_count=20)
    db.add(entry)
    db.flush()
    db.add(CompetitionAnswer(entry_id=entry.id, index=0, mode=1, question_notes=["D4"], given_notes=["D4"],
                             result="right", points=100, response_ms=800))
    db.commit()

    everyone = client.get("/api/analytics").json()
    assert everyone["answers"] == 3 and everyone["players"] == 2
    assert by(everyone["notes"], "note")["D"]["answers"] == 3

    mine = client.get("/api/analytics?scope=me").json()
    assert mine["answers"] == 1 and mine["players"] is None
    assert by(mine["notes"], "note")["D"]["accuracy"] == 1


def test_no_data_yet_and_guests_see_only_everyone(guest_client):
    data = guest_client.get("/api/analytics").json()
    assert data["answers"] == 0 and data["intervals"] == [] and data["confusions"] == []
    assert guest_client.get("/api/analytics?scope=me").status_code == 401
