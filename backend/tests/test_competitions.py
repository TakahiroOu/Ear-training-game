import uuid
from datetime import datetime

import pytest

from app import competitions as rules
from app.auth import CurrentUser
from app.models import Competition, CompetitionEntry

WRONG = ["C3", "C#3", "D3", "D#3", "E3"]  # never the answer (questions have at most 4 notes)


@pytest.fixture
def named(client):
    """Logged-in client that has chosen a username (needed to enter)."""
    assert client.patch("/api/me", json={"username": "ピアノ太郎"}).status_code == 200
    return client


def ranked_id(client, category):
    ranked = client.get("/api/competitions").json()["ranked"]
    return next(c["id"] for c in ranked if c["category"] == category)


def play_question(client, db, entry_id, index, given=None):
    """Fetch the audio (starts the timer), then answer. given=None answers correctly."""
    assert client.get(f"/api/entries/{entry_id}/audio").status_code == 200
    if given is None:
        entry = db.get(CompetitionEntry, entry_id)
        db.refresh(entry)
        _, given = rules.question(entry.seed, index, entry.competition.question_count, entry.competition.category)
    return client.post(f"/api/entries/{entry_id}/answers", json={"index": index, "given_notes": given})


def play_run(client, db, competition_id, given=None):
    entry = client.post(f"/api/competitions/{competition_id}/entries").json()
    for index in range(entry["question_count"]):
        response = play_question(client, db, entry["id"], index, given)
    return response.json()["entry"]


# ---------- rules ----------

def test_categories():
    assert [rules.mode_for(i, 20, "easy") for i in range(20)] == [1] * 20
    assert [rules.mode_for(i, 20, "mixed") for i in range(20)] == [1] * 5 + [2] * 5 + [3] * 5 + [4] * 5


def test_same_seed_same_questions():
    questions = lambda seed: [rules.question(seed, i, 20, "mixed") for i in range(20)]
    assert questions("ranked-mixed-abc") == questions("ranked-mixed-abc")
    assert questions("ranked-mixed-abc") != questions("ranked-mixed-xyz")


def test_speed_scoring():
    # 1 note: fast within 3.5 s
    assert rules.points_for("right", 1, 2000) == 150
    assert rules.points_for("right", 1, 7000) == 100  # halfway between fast (3.5 s) and slow (10.5 s)
    assert rules.points_for("right", 1, 30000) == 25  # very slow
    # 4 notes: more time allowed, and a bigger gap between fast and slow
    assert rules.points_for("right", 4, 8000) == 600
    assert rules.points_for("right", 4, 60000) == 100
    assert 600 - 100 > 150 - 25
    # wrong octave: half; wrong: minus points
    assert rules.points_for("octave", 2, 1000) == 150
    assert rules.points_for("wrong", 1, 1000) == -50
    assert rules.points_for("wrong", 4, 1000) == -200


def test_week_starts_monday_midnight_japan_time():
    # Wednesday Oct 21, 2026 10:00 UTC -> Monday Oct 19 00:00 JST = Sunday Oct 18 15:00 UTC
    assert rules.week_start(datetime(2026, 10, 21, 10, 0)) == datetime(2026, 10, 18, 15, 0)


# ---------- API: ranked ----------

def test_guests_see_ranked_competitions(guest_client):
    ranked = guest_client.get("/api/competitions").json()["ranked"]
    assert [(c["kind"], c["category"]) for c in ranked] == [("ranked", "easy"), ("ranked", "mixed")]
    assert guest_client.get(f"/api/competitions/{ranked[0]['id']}/leaderboard").status_code == 200
    assert guest_client.post(f"/api/competitions/{ranked[0]['id']}/entries").status_code == 401


def test_listing_twice_does_not_create_duplicates(guest_client, db):
    guest_client.get("/api/competitions")
    guest_client.get("/api/competitions")
    assert db.query(Competition).count() == 2


def test_username_is_required_and_unique(client, login_as):
    competition_id = ranked_id(client, "easy")
    assert client.post(f"/api/competitions/{competition_id}/entries").json()["detail"] == "username_required"
    assert client.patch("/api/me", json={"username": "a"}).status_code == 422  # too short
    assert client.patch("/api/me", json={"username": "taro"}).status_code == 200
    login_as(CurrentUser(id=uuid.uuid4(), email="other@example.com"))
    assert client.patch("/api/me", json={"username": "taro"}).json()["detail"] == "username_taken"


def test_easy_run_is_all_single_notes_and_scores_speed(named, db):
    competition_id = ranked_id(named, "easy")
    entry = named.post(f"/api/competitions/{competition_id}/entries").json()
    assert entry["next_mode"] == 1 and entry["question_count"] == 20

    audio = named.get(f"/api/entries/{entry['id']}/audio")
    assert audio.headers["content-type"] == "audio/wav" and audio.content[:4] == b"RIFF"

    first = play_question(named, db, entry["id"], 0).json()
    assert first["result"] == "right" and first["points"] == 150  # answered within a second
    wrong = play_question(named, db, entry["id"], 1, given=WRONG[:1] + ["F3"]).json()
    assert wrong["result"] == "wrong" and wrong["points"] == -50
    assert wrong["entry"]["score"] == 100


def test_play_anytime_as_often_as_you_like(named, db):
    competition_id = ranked_id(named, "mixed")
    first = play_run(named, db, competition_id)
    assert first["finished"] and first["rank"] == 1
    second = named.post(f"/api/competitions/{competition_id}/entries").json()
    assert second["id"] != first["id"] and second["next_index"] == 0  # a new run
    # ... with new questions
    seeds = [e.seed for e in db.query(CompetitionEntry).order_by(CompetitionEntry.id)]
    assert len(set(seeds)) == 2

    # a started run is continued, not replaced
    assert named.post(f"/api/competitions/{competition_id}/entries").json()["id"] == second["id"]


def test_leaderboard_shows_each_players_best_run(named, db, login_as):
    competition_id = ranked_id(named, "easy")
    play_run(named, db, competition_id, given=WRONG)  # bad run: -1000
    play_run(named, db, competition_id)  # good run

    login_as(CurrentUser(id=uuid.uuid4(), email="hanako@example.com"))
    named.patch("/api/me", json={"username": "hanako"})
    play_run(named, db, competition_id, given=WRONG)

    for period in ["all", "week"]:
        board = named.get(f"/api/competitions/{competition_id}/leaderboard?period={period}").json()
        assert [(r["rank"], r["name"]) for r in board["rows"]] == [(1, "ピアノ太郎"), (2, "hanako")]
        assert board["rows"][0]["score"] > 0 > board["rows"][1]["score"]
        assert board["me"]["name"] == "hanako" and board["me"]["is_me"] is True
    assert "@" not in str(board)  # emails are never shown

    mine = next(c for c in named.get("/api/competitions").json()["ranked"] if c["id"] == competition_id)
    assert mine["my_best"]["rank"] == 2 and mine["players"] == 2


def test_cheating_is_blocked(named, login_as):
    entry = named.post(f"/api/competitions/{ranked_id(named, 'mixed')}/entries").json()
    url = f"/api/entries/{entry['id']}/answers"
    assert named.post(url, json={"index": 0, "given_notes": ["C4"]}).json()["detail"] == "Listen to the question first"
    named.get(f"/api/entries/{entry['id']}/audio")
    assert named.post(url, json={"index": 5, "given_notes": ["C4"]}).status_code == 409  # skipping ahead
    login_as(CurrentUser(id=uuid.uuid4(), email="other@example.com"))  # someone else's run
    assert named.get(f"/api/entries/{entry['id']}/audio").status_code == 404
    assert named.post(url, json={"index": 0, "given_notes": ["C4"]}).status_code == 404


# ---------- API: class competitions ----------

def test_class_competition_with_join_code(named, db, login_as):
    created = named.post(
        "/api/competitions", json={"title": "3年A組", "category": "easy", "question_count": 8, "days": 3}
    ).json()
    code = created["join_code"]
    assert len(code) == 6 and created["kind"] == "class" and created["category"] == "easy"

    login_as(CurrentUser(id=uuid.uuid4(), email="student2@example.com"))
    found = named.get(f"/api/competitions/code/{code.lower()}").json()  # codes are not case-sensitive
    assert found["title"] == "3年A組" and found["join_code"] is None  # only the creator sees the code
    named.patch("/api/me", json={"username": "student2"})
    result = play_run(named, db, found["id"])
    assert result["finished"] and result["rank"] == 1 and result["question_count"] == 8
    # one attempt only
    again = named.post(f"/api/competitions/{found['id']}/entries")
    assert again.json()["detail"] == "You have already played this competition"
    assert [c["title"] for c in named.get("/api/competitions").json()["classes"]] == ["3年A組"]
    assert named.get("/api/competitions/code/NOPE00").status_code == 404


def test_ended_class_competition_rejects_entries(named, db):
    competition = Competition(
        kind="class", category="mixed", title="old", seed="class-old", question_count=4,
        starts_at=datetime(2020, 1, 1), ends_at=datetime(2020, 1, 2),
    )
    db.add(competition)
    db.commit()
    assert named.post(f"/api/competitions/{competition.id}/entries").json()["detail"] == "This competition is not open"
