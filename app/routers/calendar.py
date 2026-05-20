import logging

from fastapi import APIRouter, Request
from app.templating import templates
from app.services.calendar import fetch_calendar_events

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/calendar")


@router.get("/panel")
async def calendar_panel(request: Request):
    try:
        events = await fetch_calendar_events()
    except (OSError, ValueError) as e:
        logger.error("Calendar panel fetch failed: %s", e)
        return templates.TemplateResponse(request, "calendar.html", {
            "events": [],
            "error": str(e),
        })

    return templates.TemplateResponse(request, "calendar.html", {
        "events": events,
        "error": None,
    })
