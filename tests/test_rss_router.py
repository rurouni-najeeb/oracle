import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.config import FeedEntry
from app.services.feeds import FeedItem, FeedService


@pytest.fixture
def client():
    app.state.config.rss.feeds = [FeedEntry(url="https://example.com/feed.xml", name="Test")]
    app.state.feed_service = FeedService()
    return TestClient(app)


def test_rss_panel_returns_html(client):
    mock_items = [
        FeedItem(title="Article 1", link="https://example.com/1", summary="Summary 1", source="Test", published="2026-05-19 10:00", item_id="abc123"),
    ]
    with patch.object(app.state.feed_service, "fetch_all", return_value=mock_items):
        with patch.object(app.state.feed_service, "is_read", return_value=False):
            response = client.get("/rss/panel")
    assert response.status_code == 200
    assert "Article 1" in response.text


def test_rss_panel_empty_state(client):
    with patch.object(app.state.feed_service, "fetch_all", return_value=[]):
        response = client.get("/rss/panel")
    assert response.status_code == 200
    assert "No feeds configured" in response.text


def test_mark_read(client):
    mock_items = [
        FeedItem(title="Article 1", link="https://example.com/1", summary="Summary 1", source="Test", published="2026-05-19 10:00", item_id="abc123"),
    ]
    with patch.object(app.state.feed_service, "fetch_all", return_value=mock_items):
        with patch.object(app.state.feed_service, "is_read", return_value=True):
            response = client.post("/rss/mark-read/abc123")
    assert response.status_code == 200
    assert app.state.feed_service.is_read("abc123")
