from typing import Optional
from fastapi import APIRouter, Form, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from app.services.timer import PomodoroTimer

router = APIRouter(prefix="/pomodoro")
templates = Jinja2Templates(directory="app/templates")

_timer: PomodoroTimer | None = None


def _get_timer(request: Request) -> PomodoroTimer:
    global _timer
    if _timer is None:
        config = request.app.state.config.pomodoro
        _timer = PomodoroTimer(
            work_minutes=config.work_minutes,
            short_break=config.short_break_minutes,
            long_break=config.long_break_minutes,
            long_break_interval=config.sessions_before_long_break,
        )
    return _timer


@router.get("/panel")
async def panel(request: Request):
    timer = _get_timer(request)
    return templates.TemplateResponse(
        request, "pomodoro.html", {"state": timer.get_state()}
    )


@router.get("/state")
async def state(request: Request):
    timer = _get_timer(request)
    return JSONResponse(timer.get_state())


@router.post("/start")
async def start(request: Request, remaining: Optional[str] = Form(None)):
    timer = _get_timer(request)
    if remaining is not None:
        timer.remaining_seconds = int(remaining)
    timer.start()
    return templates.TemplateResponse(
        request, "pomodoro.html", {"state": timer.get_state()}
    )


@router.post("/pause")
async def pause(request: Request, remaining: Optional[str] = Form(None)):
    timer = _get_timer(request)
    if remaining is not None:
        timer.remaining_seconds = int(remaining)
    timer.pause()
    return templates.TemplateResponse(
        request, "pomodoro.html", {"state": timer.get_state()}
    )


@router.post("/reset")
async def reset(request: Request):
    timer = _get_timer(request)
    timer.reset()
    return templates.TemplateResponse(
        request, "pomodoro.html", {"state": timer.get_state()}
    )


@router.post("/skip")
async def skip(request: Request):
    timer = _get_timer(request)
    timer.skip()
    return templates.TemplateResponse(
        request, "pomodoro.html", {"state": timer.get_state()}
    )
