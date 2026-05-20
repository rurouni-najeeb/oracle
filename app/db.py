import sqlite3
import logging
from contextlib import contextmanager
from collections.abc import Generator
from pathlib import Path

DB_PATH = Path.home() / ".oracle" / "oracle.db"

logger = logging.getLogger(__name__)


@contextmanager
def get_db() -> Generator[sqlite3.Connection]:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS notes (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                created REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS read_items (
                item_id TEXT PRIMARY KEY,
                read_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS pomodoro_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                phase TEXT NOT NULL DEFAULT 'work',
                remaining_seconds INTEGER NOT NULL DEFAULT 1500,
                sessions_completed INTEGER NOT NULL DEFAULT 0,
                running INTEGER NOT NULL DEFAULT 0
            );
        """)
        conn.execute("""
            INSERT OR IGNORE INTO pomodoro_state (id, phase, remaining_seconds, sessions_completed, running)
            VALUES (1, 'work', 1500, 0, 0)
        """)
        conn.commit()
