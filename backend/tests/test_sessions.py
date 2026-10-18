import uuid

from app.auth import CurrentUser


def answer(client, session_id, mode, question, given):
    return client.post(
        f"/api/sessions/{session_id}/answers",
        json={"mode": mode, "question_notes": question, "given_notes": given, "response_ms": 1500},
    )


def test_guests_cannot_save_games(guest_client):
    assert guest_client.post("/api/sessions").status_code == 401
    assert guest_client.get("/api/me/stats").status_code == 401


def test_new_game_starts_at_zero(client):
    response = client.post("/api/sessions")
    assert response.status_code == 201
    assert response.json()["points"] == 0
    assert response.json()["mistakes"] == 0
    assert response.json()["result"] is None


def test_server_calculates_the_score(client):
    session_id = client.post("/api/sessions").json()["id"]

    right = answer(client, session_id, 3, ["C4", "E4", "G4"], ["G4", "C4", "E4"])  # any order
    assert right.json()["correct"] is True
    assert right.json()["session"]["points"] == 3

    wrong = answer(client, session_id, 3, ["C4", "E4", "G4"], ["C4", "D#4", "G4"])
    assert wrong.json()["correct"] is False
    assert wrong.json()["session"]["mistakes"] == 2


def test_wrong_octave_gives_half_points_and_no_mistakes(client):
    session_id = client.post("/api/sessions").json()["id"]
    response = answer(client, session_id, 3, ["C4", "E4", "G4"], ["C5", "E4", "G4"])
    assert response.json()["result"] == "octave"
    assert response.json()["correct"] is False
    assert response.json()["session"]["points"] == 1  # 3 // 2
    assert response.json()["session"]["mistakes"] == 0

    stats = client.get("/api/me/stats").json()
    assert stats["by_mode"] == [{"mode": 3, "answered": 1, "correct": 0, "octave": 1}]


def test_answer_saves_the_key(client, db):
    from app.models import Answer

    session_id = client.post("/api/sessions").json()["id"]
    response = client.post(
        f"/api/sessions/{session_id}/answers",
        json={"mode": 1, "key": "D-major", "question_notes": ["F#4"], "given_notes": ["F#4"]},
    )
    assert response.json()["result"] == "right"
    assert db.query(Answer).one().key == "D-major"

    bad = client.post(
        f"/api/sessions/{session_id}/answers",
        json={"mode": 1, "key": "H-major", "question_notes": ["C4"], "given_notes": ["C4"]},
    )
    assert bad.status_code == 422


def test_game_ends_at_50_points_and_then_stays_closed(client):
    session_id = client.post("/api/sessions").json()["id"]
    chord = ["C4", "E4", "G4", "A#4"]
    for _ in range(12):  # 12 x 4 = 48 points
        response = answer(client, session_id, 4, chord, chord)
    assert response.json()["session"]["result"] is None

    response = answer(client, session_id, 4, chord, chord)  # 52 points
    assert response.json()["session"]["result"] == "won"
    assert response.json()["session"]["ended_at"] is not None

    assert answer(client, session_id, 4, chord, chord).status_code == 409


def test_cannot_use_someone_elses_game(client, login_as):
    session_id = client.post("/api/sessions").json()["id"]
    login_as(CurrentUser(id=uuid.uuid4(), email="other@example.com"))
    assert answer(client, session_id, 1, ["C4"], ["C4"]).status_code == 404


def test_rejects_invalid_answers(client):
    session_id = client.post("/api/sessions").json()["id"]
    assert answer(client, session_id, 1, ["H4"], ["C4"]).status_code == 422  # no such note
    assert answer(client, session_id, 2, ["C4"], ["C4"]).status_code == 422  # 2 notes expected
    assert answer(client, session_id, 9, ["C4"], ["C4"]).status_code == 422  # no mode 9


def test_stats(client):
    session_id = client.post("/api/sessions").json()["id"]
    answer(client, session_id, 1, ["C4"], ["C4"])
    answer(client, session_id, 1, ["F#4"], ["G4"])
    answer(client, session_id, 2, ["F#4", "A3"], ["A3"])
    answer(client, session_id, 2, ["E4", "B4"], ["E4", "B4"])

    stats = client.get("/api/me/stats").json()
    assert stats["games_played"] == 1
    assert stats["wins"] == 0
    assert stats["by_mode"] == [
        {"mode": 1, "answered": 2, "correct": 1, "octave": 0},
        {"mode": 2, "answered": 2, "correct": 1, "octave": 0},
    ]
    assert stats["most_missed_notes"][0] == {"note": "F#4", "missed": 2}
    assert stats["recent_sessions"][0]["id"] == session_id


def test_stats_only_show_your_own_games(client, login_as):
    session_id = client.post("/api/sessions").json()["id"]
    answer(client, session_id, 1, ["C4"], ["C4"])

    login_as(CurrentUser(id=uuid.uuid4(), email="other@example.com"))
    stats = client.get("/api/me/stats").json()
    assert stats["games_played"] == 0
    assert stats["by_mode"] == []


def test_rls_is_on_for_every_table(db):
    from sqlalchemy import text

    tables = db.execute(text("SELECT relname FROM pg_class WHERE relrowsecurity")).scalars().all()
    assert {"profiles", "game_sessions", "answers", "alembic_version"} <= set(tables)
