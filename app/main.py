from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.config import load_config, AppConfig
from app.routers import dashboard, tasks, pomodoro, rss
from app.services.feeds import FeedService

CONFIG_PATH = Path("config.yaml")

app = FastAPI(title="Oracle Dashboard")
app.mount("/static", StaticFiles(directory="static"), name="static")

app.state.config = load_config(CONFIG_PATH)
app.state.feed_service = FeedService(
    cache_ttl_seconds=app.state.config.rss.refresh_interval_minutes * 60
)

app.include_router(dashboard.router)
app.include_router(tasks.router)
app.include_router(pomodoro.router)
app.include_router(rss.router)
