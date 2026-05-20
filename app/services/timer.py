import logging
import sqlite3
from enum import Enum

logger = logging.getLogger(__name__)


class Phase(str, Enum):
    WORK = "work"
    SHORT_BREAK = "short_break"
    LONG_BREAK = "long_break"


class PomodoroTimer:
    def __init__(
        self,
        work_minutes: int,
        short_break: int,
        long_break: int,
        long_break_interval: int,
    ):
        self.work_minutes = work_minutes
        self.short_break = short_break
        self.long_break = long_break
        self.long_break_interval = long_break_interval
        self.phase = Phase.WORK
        self.remaining_seconds = work_minutes * 60
        self.running = False
        self.sessions_completed = 0
        self._load_state()

    def _load_state(self) -> None:
        try:
            from app.db import get_db

            with get_db() as conn:
                row = conn.execute(
                    "SELECT phase, remaining_seconds, sessions_completed FROM pomodoro_state WHERE id = 1"
                ).fetchone()
                if row:
                    self.phase = Phase(row["phase"])
                    self.remaining_seconds = row["remaining_seconds"]
                    self.sessions_completed = row["sessions_completed"]
        except sqlite3.Error as e:
            logger.warning("Failed to load pomodoro state: %s", e)

    def _save_state(self) -> None:
        try:
            from app.db import get_db

            with get_db() as conn:
                conn.execute(
                    "UPDATE pomodoro_state SET phase = ?, remaining_seconds = ?, sessions_completed = ?, running = ? WHERE id = 1",
                    (
                        self.phase.value,
                        self.remaining_seconds,
                        self.sessions_completed,
                        int(self.running),
                    ),
                )
                conn.commit()
        except sqlite3.Error as e:
            logger.warning("Failed to save pomodoro state: %s", e)

    def start(self) -> None:
        self.running = True
        self._save_state()

    def pause(self) -> None:
        self.running = False
        self._save_state()

    def reset(self) -> None:
        self.running = False
        self.remaining_seconds = self._duration_for_phase(self.phase)
        self._save_state()

    def skip(self) -> None:
        if self.phase == Phase.WORK:
            self.sessions_completed += 1
            if self.sessions_completed % self.long_break_interval == 0:
                self.phase = Phase.LONG_BREAK
            else:
                self.phase = Phase.SHORT_BREAK
        else:
            self.phase = Phase.WORK
        self.remaining_seconds = self._duration_for_phase(self.phase)
        self.running = False
        self._save_state()

    def get_state(self) -> dict:
        return {
            "phase": self.phase.value,
            "remaining_seconds": self.remaining_seconds,
            "running": self.running,
            "sessions_completed": self.sessions_completed,
        }

    def _duration_for_phase(self, phase: Phase) -> int:
        if phase == Phase.WORK:
            return self.work_minutes * 60
        elif phase == Phase.SHORT_BREAK:
            return self.short_break * 60
        else:
            return self.long_break * 60
