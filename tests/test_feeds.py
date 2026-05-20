from unittest.mock import patch, MagicMock
from app.services.feeds import FeedService


def _mock_feed_response():
    mock_feed = MagicMock()
    mock_feed.bozo = False
    mock_feed.entries = [
        MagicMock(
            title="Test Article",
            link="https://example.com/article",
            published_parsed=(2026, 5, 19, 10, 0, 0, 0, 139, 0),
            get=lambda k, d=None: {
                "summary": "This is a test article summary that is long enough.",
                "title": "Test Article",
                "link": "https://example.com/article",
            }.get(k, d),
        ),
    ]
    mock_feed.feed = MagicMock(title="Test Blog")
    return mock_feed


def test_fetch_feeds_returns_items():
    service = FeedService()
    with patch(
        "app.services.feeds.feedparser.parse", return_value=_mock_feed_response()
    ):
        items = service.fetch_feed("https://example.com/feed.xml", "Test Blog")
    assert len(items) == 1
    assert items[0].title == "Test Article"
    assert items[0].link == "https://example.com/article"
    assert items[0].source == "Test Blog"


def test_fetch_feeds_caches_results():
    service = FeedService()
    mock_resp = _mock_feed_response()
    with patch(
        "app.services.feeds.feedparser.parse", return_value=mock_resp
    ) as mock_parse:
        service.fetch_feed("https://example.com/feed.xml", "Test Blog")
        service.fetch_feed("https://example.com/feed.xml", "Test Blog")
    assert mock_parse.call_count == 1


def test_fetch_feeds_respects_ttl():
    service = FeedService(cache_ttl_seconds=0)
    mock_resp = _mock_feed_response()
    with patch(
        "app.services.feeds.feedparser.parse", return_value=mock_resp
    ) as mock_parse:
        service.fetch_feed("https://example.com/feed.xml", "Test Blog")
        service.fetch_feed("https://example.com/feed.xml", "Test Blog")
    assert mock_parse.call_count == 2


def test_mark_read():
    service = FeedService()
    service.mark_read("item-123")
    assert service.is_read("item-123")
    assert not service.is_read("item-456")
