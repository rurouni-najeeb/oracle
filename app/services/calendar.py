import asyncio
import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class CalendarEvent:
    title: str
    start: datetime
    end: datetime
    location: str
    minutes_until: int
    is_now: bool
    day_label: str


@dataclass
class _CacheEntry:
    result: list[CalendarEvent]
    ts: float


_cache: _CacheEntry | None = None
_cache_ttl: int = 60

CALENDAR_SWIFT = """\
import EventKit
import Foundation

let store = EKEventStore()
let semaphore = DispatchSemaphore(value: 0)
store.requestFullAccessToEvents { _, _ in semaphore.signal() }
semaphore.wait()

let now = Date()
let calendar = Calendar.current
let startOfToday = calendar.startOfDay(for: now)
let endOfTomorrow = calendar.date(byAdding: .day, value: 2, to: startOfToday)!

let predicate = store.predicateForEvents(withStart: startOfToday, end: endOfTomorrow, calendars: nil)
let events = store.events(matching: predicate)

var results: [[String: String]] = []
let formatter = ISO8601DateFormatter()

for event in events {
    results.append([
        "title": event.title ?? "",
        "start": formatter.string(from: event.startDate),
        "end": formatter.string(from: event.endDate),
        "location": event.location ?? ""
    ])
}

let data = try! JSONSerialization.data(withJSONObject: results, options: [])
print(String(data: data, encoding: .utf8)!)
"""


async def fetch_calendar_events() -> list[CalendarEvent]:
    global _cache
    if _cache and (time.time() - _cache.ts) < _cache_ttl:
        return _cache.result

    try:
        proc = await asyncio.create_subprocess_exec(
            "swift", "-e", CALENDAR_SWIFT,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        output = stdout.decode().strip()
        if not output:
            if stderr:
                logger.warning("Calendar script error: %s", stderr.decode().strip())
            return []

        items: list[dict[str, str]] = json.loads(output)
    except (OSError, json.JSONDecodeError) as e:
        logger.warning("Failed to fetch calendar events: %s", e)
        return []

    now = datetime.now()
    today = now.date()
    events: list[CalendarEvent] = []
    for item in items:
        start_utc = datetime.fromisoformat(item["start"].replace("Z", "+00:00"))
        end_utc = datetime.fromisoformat(item["end"].replace("Z", "+00:00"))
        start = start_utc.astimezone().replace(tzinfo=None)
        end = end_utc.astimezone().replace(tzinfo=None)
        minutes_until = int((start - now).total_seconds() / 60)
        is_now = start <= now <= end
        day_label = "Today" if start.date() == today else "Tomorrow"

        events.append(CalendarEvent(
            title=item["title"],
            start=start,
            end=end,
            location=item.get("location", ""),
            minutes_until=minutes_until,
            is_now=is_now,
            day_label=day_label,
        ))

    events = [e for e in events if e.end > now]
    seen: set[tuple[str, str]] = set()
    unique: list[CalendarEvent] = []
    for e in events:
        key = (e.title, e.start.isoformat())
        if key not in seen:
            seen.add(key)
            unique.append(e)
    events = unique
    _cache = _CacheEntry(result=events, ts=time.time())
    return events
