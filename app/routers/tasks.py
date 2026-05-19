from datetime import date
from pathlib import Path
from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from app.services.vault import scan_tasks, toggle_task, add_task

router = APIRouter(prefix="/tasks")
templates = Jinja2Templates(directory="app/templates")


@router.get("/panel")
async def tasks_panel(request: Request):
    config = request.app.state.config
    vault_path = config.tasks.vault_path
    if not vault_path or not vault_path.exists():
        return templates.TemplateResponse(request, "tasks.html", {"tasks": [], "error": "Vault path not configured"})
    all_tasks = scan_tasks(vault_path)
    incomplete = [t for t in all_tasks if not t.completed]
    return templates.TemplateResponse(request, "tasks.html", {"tasks": incomplete})


@router.post("/toggle")
async def toggle(request: Request, file: str = Form(...), line: str = Form(...)):
    toggle_task(Path(file), int(line))
    return await tasks_panel(request)


@router.post("/add")
async def add(request: Request, text: str = Form(...)):
    config = request.app.state.config
    vault_path = config.tasks.vault_path
    inbox = config.tasks.inbox_file
    if inbox == "daily":
        target = vault_path / f"{date.today().isoformat()}.md"
    else:
        target = vault_path / inbox
    add_task(target, text)
    return await tasks_panel(request)
