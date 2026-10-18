from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_question_has_requested_number_of_notes():
    response = client.get("/api/questions?mode=3")
    assert response.status_code == 200
    assert response.json()["mode"] == 3
    assert len(response.json()["notes"]) == 3


def test_question_rejects_unknown_mode():
    assert client.get("/api/questions?mode=5").status_code == 422
    assert client.get("/api/questions?mode=0").status_code == 422

