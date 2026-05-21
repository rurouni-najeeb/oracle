import pytest
from fastapi.testclient import TestClient

from app.config import GitHubConfig, build_github_repository
from app.main import app
from app.routers import github as github_router


@pytest.fixture
def client(tmp_path, monkeypatch):
    original_github = app.state.config.github
    app.state.config.github = GitHubConfig(
        orgs=["moia-dev"],
        repositories=[build_github_repository("moia-dev/oracle", "Oracle")],
    )
    monkeypatch.setattr(github_router, "CONFIG_PATH", tmp_path / "config.yaml")
    yield TestClient(app)
    app.state.config.github = original_github


def test_repositories_panel_returns_shortcuts(client):
    response = client.get("/github/repositories/panel")

    assert response.status_code == 200
    assert "Oracle" in response.text
    assert "https://github.com/moia-dev/oracle/pulls" in response.text
    assert "https://github.com/moia-dev/oracle/actions" in response.text
    assert "https://github.com/moia-dev/oracle/issues" in response.text


def test_add_repository_from_owner_repo(client):
    response = client.post(
        "/github/repositories/add",
        data={"repository": "moia-dev/dispatch", "display_name": "Dispatch"},
    )

    assert response.status_code == 200
    assert "Dispatch" in response.text
    assert "https://github.com/moia-dev/dispatch" in response.text
    assert app.state.config.github.repositories[-1].full_name == "moia-dev/dispatch"


def test_invalid_repository_returns_panel_error(client):
    response = client.post(
        "/github/repositories/add",
        data={"repository": "https://example.com/not-github"},
    )

    assert response.status_code == 200
    assert "Use a GitHub repository URL." in response.text
