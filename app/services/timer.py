from enum import Enum


class Phase(str, Enum):
    WORK = "work"
    SHORT_BREAK = "short_break"
    LONG_BREAK = "long_break"


class PomodoroTimer:
    def __init__(self, work_minutes: int, short_break: int, long_break: int, long_break_interval: int):
        self.work_minutes = work_minutes
        self.short_break = short_break
        self.long_break = long_break
        self.long_break_interval = long_break_interval
        self.phase = Phase.WORK
        self.remaining_seconds = work_minutes * 60
        self.running = False
        self.sessions_completed = 0

    def start(self) -> None:
        self.running = True

    def pause(self) -> None:
        self.running = False

    def reset(self) -> None:
        self.running = False
        self.remaining_seconds = self._duration_for_phase(self.phase)

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
