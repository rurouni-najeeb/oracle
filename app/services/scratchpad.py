import time
from dataclasses import dataclass
from app.db import get_db


@dataclass
class Note:
    id: str
    content: str
    created: float


def get_notes() -> list[Note]:
    with get_db() as conn:
        rows = conn.execute("SELECT id, content, created FROM notes ORDER BY created DESC").fetchall()
        return [Note(id=r["id"], content=r["content"], created=r["created"]) for r in rows]


def add_note(content: str) -> None:
    note_id = f"n_{int(time.time() * 1000)}"
    with get_db() as conn:
        conn.execute("INSERT INTO notes (id, content, created) VALUES (?, ?, ?)", (note_id, content, time.time()))
        conn.commit()


def update_note(note_id: str, content: str) -> None:
    with get_db() as conn:
        conn.execute("UPDATE notes SET content = ? WHERE id = ?", (content, note_id))
        conn.commit()


def delete_note(note_id: str) -> None:
    with get_db() as conn:
        conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        conn.commit()
