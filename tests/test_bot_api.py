"""Light Flask API tests for the bot service (mocked Groq)."""

import pytest

from gamemode import app, GAMES_DB


@pytest.fixture
def client():
    app.config["TESTING"] = True
    GAMES_DB.clear()
    with app.test_client() as test_client:
        yield test_client


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_start_match_cpu(client):
    response = client.post("/api/start_match", json={"mode": "cpu"})
    assert response.status_code == 201
    data = response.get_json()
    assert "game_id" in data


def test_get_bot_move_cpu(client):
    board = [""] * 25
    response = client.post(
        "/api/get_bot_move",
        json={"mode": "cpu", "board_state": board},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "move" in data
    assert isinstance(data["move"], int)
    assert 0 <= data["move"] < 25
