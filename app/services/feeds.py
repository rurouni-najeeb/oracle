import html
import logging
import re
import time
import hashlib
from dataclasses import dataclass
import feedparser

logger = logging.getLogger(__name__)

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")
_SAFE_URL_SCHEMES = {"http", "https", ""}


def _safe_link(url: str) -> str:
    scheme = url.split(":", 1)[0].lower() if ":" in url else ""
    if scheme in _SAFE_URL_SCHEMES:
        return url
    return ""


def _strip_html(text: str) -> str:
    text = _HTML_TAG_RE.sub(" ", text)
    text = html.unescape(text)
    text = _WHITESPACE_RE.sub(" ", text)
    return text.strip()


@dataclass
class FeedItem:
    title: str
    link: str
    summary: str
    source: str
    published: str
    item_id: str


class FeedService:
    def __init__(self, cache_ttl_seconds: int = 300):
        self._cache: dict[str, tuple[float, list[FeedItem]]] = {}
        self._cache_ttl = cache_ttl_seconds

    def fetch_feed(self, url: str, name: str) -> list[FeedItem]:
        now = time.time()
        if url in self._cache:
            cached_time, cached_items = self._cache[url]
            if now - cached_time < self._cache_ttl:
                return cached_items

        parsed = feedparser.parse(url)
        items = []
        for entry in parsed.entries:
            item_id = hashlib.md5(
                (entry.get("link", "") + entry.get("title", "")).encode()
            ).hexdigest()
            summary = _strip_html(entry.get("summary", ""))
            if len(summary) > 150:
                summary = summary[:150] + "..."
            pub = ""
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                pub = time.strftime("%Y-%m-%d %H:%M", entry.published_parsed)
            items.append(
                FeedItem(
                    title=entry.get("title", "Untitled"),
                    link=_safe_link(entry.get("link", "")),
                    summary=summary,
                    source=name,
                    published=pub,
                    item_id=item_id,
                )
            )
        self._cache[url] = (now, items)
        return items

    def fetch_all(self, feeds: list[dict]) -> list[FeedItem]:
        all_items = []
        for feed in feeds:
            try:
                items = self.fetch_feed(feed["url"], feed["name"])
                all_items.extend(items)
            except (OSError, KeyError, ValueError) as e:
                logger.warning(
                    "Failed to fetch feed %s: %s", feed.get("name", "unknown"), e
                )
                continue
        all_items.sort(key=lambda x: x.published, reverse=True)
        return all_items

    def mark_read(self, item_id: str) -> None:
        from app.db import get_db

        with get_db() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO read_items (item_id, read_at) VALUES (?, ?)",
                (item_id, time.time()),
            )
            conn.commit()

    def is_read(self, item_id: str) -> bool:
        from app.db import get_db

        with get_db() as conn:
            row = conn.execute(
                "SELECT 1 FROM read_items WHERE item_id = ?", (item_id,)
            ).fetchone()
            return row is not None
