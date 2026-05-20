import pytest
from fastapi.testclient import TestClient
import app.db as db_module
from app.main import app as fastapi_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", tmp_path / "test.db")
    db_module.init_db()
    from app.routers import pomodoro

    pomodoro._timer = None
    return TestClient(fastapi_app)


def test_pomodoro_panel_returns_html(client):
    response = client.get("/pomodoro/panel")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_pomodoro_state_returns_json(client):
    response = client.get("/pomodoro/state")
    assert response.status_code == 200
    data = response.json()
    assert "phase" in data
    assert "remaining_seconds" in data
    assert "running" in data


def test_pomodoro_start(client):
    response = client.post("/pomodoro/start")
    assert response.status_code == 200
    state = client.get("/pomodoro/state").json()
    assert state["running"] is True


def test_pomodoro_pause(client):
    client.post("/pomodoro/start")
    response = client.post("/pomodoro/pause")
    assert response.status_code == 200
    state = client.get("/pomodoro/state").json()
    assert state["running"] is False


def test_pomodoro_reset(client):
    client.post("/pomodoro/start")
    response = client.post("/pomodoro/reset")
    assert response.status_code == 200
    state = client.get("/pomodoro/state").json()
    assert state["running"] is False
    assert state["remaining_seconds"] == 25 * 60


def test_pomodoro_skip(client):
    response = client.post("/pomodoro/skip")
    assert response.status_code == 200
    state = client.get("/pomodoro/state").json()
    assert state["phase"] == "short_break"
