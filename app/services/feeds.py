import time
import hashlib
from dataclasses import dataclass
import feedparser


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
        self._read_items: set[str] = set()
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
            item_id = hashlib.md5((entry.get("link", "") + entry.get("title", "")).encode()).hexdigest()
            summary = entry.get("summary", "")
            if len(summary) > 150:
                summary = summary[:150] + "..."
            pub = ""
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                pub = time.strftime("%Y-%m-%d %H:%M", entry.published_parsed)
            items.append(FeedItem(
                title=entry.get("title", "Untitled"),
                link=entry.get("link", ""),
                summary=summary,
                source=name,
                published=pub,
                item_id=item_id,
            ))
        self._cache[url] = (now, items)
        return items

    def fetch_all(self, feeds: list[dict]) -> list[FeedItem]:
        all_items = []
        for feed in feeds:
            try:
                items = self.fetch_feed(feed["url"], feed["name"])
                all_items.extend(items)
            except Exception:
                continue
        all_items.sort(key=lambda x: x.published, reverse=True)
        return all_items

    def mark_read(self, item_id: str) -> None:
        self._read_items.add(item_id)

    def is_read(self, item_id: str) -> bool:
        return item_id in self._read_items
