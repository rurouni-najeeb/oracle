import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client_with_vault(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "note.md").write_text("- [ ] Test task #task\n- [x] Done task #task\n")
    app.state.config.tasks.vault_path = vault
    app.state.config.tasks.inbox_file = "inbox.md"
    return TestClient(app)


def test_tasks_panel_returns_html(client_with_vault):
    response = client_with_vault.get("/tasks/panel")
    assert response.status_code == 200
    assert "Test task" in response.text
    assert "text/html" in response.headers["content-type"]


def test_toggle_task(client_with_vault, tmp_path):
    vault = tmp_path / "vault"
    response = client_with_vault.post(
        "/tasks/toggle",
        data={"file": str(vault / "note.md"), "line": "1"},
    )
    assert response.status_code == 200
    content = (vault / "note.md").read_text()
    assert "- [x] Test task #task" in content


def test_add_task(client_with_vault, tmp_path):
    vault = tmp_path / "vault"
    response = client_with_vault.post(
        "/tasks/add",
        data={"text": "New task from dashboard"},
    )
    assert response.status_code == 200
    inbox = vault / "inbox.md"
    assert inbox.exists()
    assert "New task from dashboard" in inbox.read_text()
