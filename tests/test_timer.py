import pytest
from app.services.timer import PomodoroTimer, Phase


@pytest.fixture(autouse=True)
def isolate_db(tmp_path, monkeypatch):
    import app.db

    monkeypatch.setattr(app.db, "DB_PATH", tmp_path / "test.db")
    app.db.init_db()


def test_initial_state():
    timer = PomodoroTimer(
        work_minutes=25, short_break=5, long_break=15, long_break_interval=4
    )
    assert timer.phase == Phase.WORK
    assert timer.remaining_seconds == 25 * 60
    assert timer.running is False
    assert timer.sessions_completed == 0


def test_start():
    timer = PomodoroTimer(
        work_minutes=25, short_break=5, long_break=15, long_break_interval=4
    )
    timer.start()
    assert timer.running is True


def test_pause():
    timer = PomodoroTimer(
        work_minutes=25, short_break=5, long_break=15, long_break_interval=4
    )
    timer.start()
    timer.pause()
    assert timer.running is False


def test_reset():
    timer = PomodoroTimer(
        work_minutes=25, short_break=5, long_break=15, long_break_interval=4
    )
    timer.start()
    timer.remaining_seconds = 100
    timer.reset()
    assert timer.remaining_seconds == 25 * 60
    assert timer.running is False


def test_skip_from_work_to_short_break():
    timer = PomodoroTimer(
        work_minutes=25, short_break=5, long_break=15, long_break_interval=4
    )
    timer.skip()
    assert timer.phase == Phase.SHORT_BREAK
    assert timer.remaining_seconds == 5 * 60
    assert timer.sessions_completed == 1


def test_skip_from_break_to_work():
    timer = PomodoroTimer(
        work_minutes=25, short_break=5, long_break=15, long_break_interval=4
    )
    timer.skip()  # work -> short break
    timer.skip()  # short break -> work
    assert timer.phase == Phase.WORK
    assert timer.remaining_seconds == 25 * 60


def test_long_break_after_interval():
    timer = PomodoroTimer(
        work_minutes=25, short_break=5, long_break=15, long_break_interval=4
    )
    for i in range(3):
        timer.skip()  # work -> short break (sessions: i+1)
        timer.skip()  # break -> work
    timer.skip()  # 4th work -> should be long break
    assert timer.phase == Phase.LONG_BREAK
    assert timer.remaining_seconds == 15 * 60
    assert timer.sessions_completed == 4


def test_get_state():
    timer = PomodoroTimer(
        work_minutes=25, short_break=5, long_break=15, long_break_interval=4
    )
    state = timer.get_state()
    assert state["phase"] == "work"
    assert state["remaining_seconds"] == 1500
    assert state["running"] is False
    assert state["sessions_completed"] == 0
