from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/rss")
templates = Jinja2Templates(directory="app/templates")


@router.get("/panel")
async def rss_panel(request: Request):
    feed_service = request.app.state.feed_service
    config = request.app.state.config
    feeds = [{"url": f.url, "name": f.name} for f in config.rss.feeds]
    items = feed_service.fetch_all(feeds)
    items_with_read = [
        {**item.__dict__, "is_read": feed_service.is_read(item.item_id)}
        for item in items
    ]
    return templates.TemplateResponse(request, "rss.html", {"items": items_with_read})


@router.post("/mark-read/{item_id}")
async def mark_read(request: Request, item_id: str):
    feed_service = request.app.state.feed_service
    feed_service.mark_read(item_id)
    return await rss_panel(request)
