import uuid
from datetime import datetime, timedelta

import pytest

from app import competitions as rules
from app.auth import CurrentUser
from app.models import Competition


@pytest.fixture
def named(client):
    """Logged-in client that has chosen a username (needed to enter)."""
    assert client.patch("/api/me", json={"username": "ピアノ太郎"}).status_code == 200
    return client


def daily_id(client):
    current = client.get("/api/competitions").json()["current"]
    return next(c["id"] for c in current if c["kind"] == "daily")


def play_question(client, entry_id, index, given=None):
    """Fetch the audio (starts the timer), then answer. given=None answers correctly."""
    assert client.get(f"/api/entries/{entry_id}/audio").status_code == 200
    if given is None:
        from app.db import get_db
        from app.main import app

        db = app.dependency_overrides[get_db]()  # the test database session (see conftest.py)
        entry = db.get(rules.CompetitionEntry, entry_id)
        _, given = rules.question(entry.competition, index)
    return client.post(f"/api/entries/{entry_id}/answers", json={"index": index, "given_notes": given})


# ---------- rules ----------

def test_periods_start_at_midnight_japan_time():
    now = datetime(2026, 10, 18, 16, 30)  # 01:30 on Oct 19 in Japan
    (daily, daily_seed, d_start, d_end), (weekly, w_seed, w_start, _), (monthly, m_seed, _, m_end) = (
        rules.current_periods(now)
    )
    assert daily_seed == "daily-2026-10-19"
    assert rules.to_utc(d_start) == datetime(2026, 10, 18, 15, 0)  # midnight JST = 15:00 UTC
    assert d_end - d_start == timedelta(days=1)
    assert w_seed == "weekly-2026-10-19"  # Oct 19, 2026 is a Monday
    assert m_seed == "monthly-2026-10"
    assert m_end.month == 11 and m_end.day == 1


def test_same_seed_same_questions_and_harder_later():
    competition = Competition(seed="daily-2026-10-18", question_count=20)
    assert [rules.question(competition, i) for i in range(20)] == [rules.question(competition, i) for i in range(20)]
    assert [rules.mode_for(i, 20) for i in range(20)] == [1] * 5 + [2] * 5 + [3] * 5 + [4] * 5
    other = Competition(seed="daily-2026-10-19", question_count=20)
    assert [rules.question(competition, i) for i in range(20)] != [rules.question(other, i) for i in range(20)]


def test_points():
    assert rules.points_for("right", 3) == 300
    assert rules.points_for("octave", 3) == 150
    assert rules.points_for("wrong", 3) == 0


# ---------- API ----------

def test_guests_can_see_competitions_and_leaderboards(guest_client):
    current = guest_client.get("/api/competitions").json()["current"]
    assert [c["kind"] for c in current] == ["daily", "weekly", "monthly"]
    assert all(c["active"] and c["my_entry"] is None for c in current)
    assert guest_client.get(f"/api/competitions/{current[0]['id']}/leaderboard").status_code == 200
    assert guest_client.post(f"/api/competitions/{current[0]['id']}/entries").status_code == 401


def test_listing_twice_does_not_create_duplicates(guest_client, db):
    guest_client.get("/api/competitions")
    guest_client.get("/api/competitions")
    assert db.query(Competition).count() == 3


def test_username_is_required_and_unique(client, login_as):
    assert client.post(f"/api/competitions/{daily_id(client)}/entries").json()["detail"] == "username_required"
    assert client.patch("/api/me", json={"username": "a"}).status_code == 422  # too short
    assert client.patch("/api/me", json={"username": "taro"}).status_code == 200
    login_as(CurrentUser(id=uuid.uuid4(), email="other@example.com"))
    assert client.patch("/api/me", json={"username": "taro"}).json()["detail"] == "username_taken"


def test_play_a_whole_competition(named):
    entry = named.post(f"/api/competitions/{daily_id(named)}/entries").json()
    assert entry["next_index"] == 0 and entry["next_mode"] == 1 and entry["question_count"] == 20

    # The audio is a WAV clip, and no note names are sent before answering
    audio = named.get(f"/api/entries/{entry['id']}/audio")
    assert audio.headers["content-type"] == "audio/wav" and audio.content[:4] == b"RIFF"

    first = play_question(named, entry["id"], 0)
    assert first.json()["result"] == "right"
    assert first.json()["points"] == 100
    second = play_question(named, entry["id"], 1, given=["C3", "C#3"])
    assert second.json()["points"] in (0, 50)  # wrong (or, by chance, right letter in the wrong octave)
    for index in range(2, 20):
        response = play_question(named, entry["id"], index)
    final = response.json()["entry"]
    assert final["finished"] is True and final["rank"] == 1 and final["correct"] >= 19

    # Only one attempt
    again = named.post(f"/api/competitions/{daily_id(named)}/entries").json()
    assert again["id"] == entry["id"] and again["finished"] is True
    assert named.get(f"/api/entries/{entry['id']}/audio").status_code == 409


def test_cheating_is_blocked(named, login_as):
    entry = named.post(f"/api/competitions/{daily_id(named)}/entries").json()
    url = f"/api/entries/{entry['id']}/answers"
    # answering before listening
    assert named.post(url, json={"index": 0, "given_notes": ["C4"]}).json()["detail"] == "Listen to the question first"
    named.get(f"/api/entries/{entry['id']}/audio")
    # skipping ahead
    assert named.post(url, json={"index": 5, "given_notes": ["C4"]}).status_code == 409
    # someone else's entry
    login_as(CurrentUser(id=uuid.uuid4(), email="other@example.com"))
    assert named.get(f"/api/entries/{entry['id']}/audio").status_code == 404
    assert named.post(url, json={"index": 0, "given_notes": ["C4"]}).status_code == 404


def test_leaderboard_order_and_names(named, login_as, user):
    competition_id = daily_id(named)
    # Player 1 (ピアノ太郎) answers everything right
    entry = named.post(f"/api/competitions/{competition_id}/entries").json()
    for index in range(20):
        play_question(named, entry["id"], index)

    # Player 2 has no ranking yet while playing, then answers everything wrong
    other = CurrentUser(id=uuid.uuid4(), email="hanako@example.com")
    login_as(other)
    named.patch("/api/me", json={"username": "hanako"})
    entry2 = named.post(f"/api/competitions/{competition_id}/entries").json()
    for index in range(20):
        play_question(named, entry2["id"], index, given=["C3", "C#3", "D3", "D#3", "E3"])

    board = named.get(f"/api/competitions/{competition_id}/leaderboard").json()
    assert [(r["rank"], r["name"]) for r in board["rows"]] == [(1, "ピアノ太郎"), (2, "hanako")]
    assert board["me"]["name"] == "hanako" and board["me"]["is_me"] is True
    assert "@" not in str(board)  # emails are never shown


def test_ended_competition_rejects_new_entries(named, db):
    competition = Competition(
        kind="class", title="old", seed="class-old", question_count=4,
        starts_at=datetime(2020, 1, 1), ends_at=datetime(2020, 1, 2),
    )
    db.add(competition)
    db.commit()
    assert named.post(f"/api/competitions/{competition.id}/entries").json()["detail"] == "This competition is not open"


def test_class_competition_with_join_code(named, login_as):
    created = named.post("/api/competitions", json={"title": "3年A組", "question_count": 8, "days": 3}).json()
    code = created["join_code"]
    assert len(code) == 6 and created["kind"] == "class"

    student = CurrentUser(id=uuid.uuid4(), email="student2@example.com")
    login_as(student)
    found = named.get(f"/api/competitions/code/{code.lower()}").json()  # codes are not case-sensitive
    assert found["title"] == "3年A組" and found["join_code"] is None  # only the creator sees the code
    named.patch("/api/me", json={"username": "student2"})
    entry = named.post(f"/api/competitions/{found['id']}/entries").json()
    assert entry["question_count"] == 8
    assert [c["title"] for c in named.get("/api/competitions").json()["classes"]] == ["3年A組"]

    assert named.get("/api/competitions/code/NOPE00").status_code == 404
