from pathlib import Path
from fastapi import APIRouter, Request, Form
from app.templating import templates
from app.config import FeedEntry, save_config

router = APIRouter(prefix="/rss")

CONFIG_PATH = Path("config.yaml")


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
    return templates.TemplateResponse(
        request,
        "rss.html",
        {
            "items": items_with_read,
            "feeds": config.rss.feeds,
        },
    )


@router.post("/mark-read/{item_id}")
async def mark_read(request: Request, item_id: str):
    feed_service = request.app.state.feed_service
    feed_service.mark_read(item_id)
    return await rss_panel(request)


@router.post("/add-feed")
async def add_feed(request: Request, url: str = Form(...), name: str = Form("")):
    config = request.app.state.config
    feed_name = name or url.split("/")[2] if "/" in url else url
    config.rss.feeds.append(FeedEntry(url=url, name=feed_name))
    save_config(config, CONFIG_PATH)
    return await rss_panel(request)


@router.post("/remove-feed")
async def remove_feed(request: Request, url: str = Form(...)):
    config = request.app.state.config
    config.rss.feeds = [f for f in config.rss.feeds if f.url != url]
    save_config(config, CONFIG_PATH)
    return await rss_panel(request)
