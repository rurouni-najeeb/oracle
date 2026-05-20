from datetime import date
from itertools import groupby
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request, Form
from app.templating import templates
from app.services.vault import scan_tasks, toggle_task, add_task

router = APIRouter(prefix="/tasks")


def _validate_vault_path(file: Path, vault_path: Path) -> None:
    resolved = file.resolve()
    vault_resolved = vault_path.resolve()
    if not str(resolved).startswith(str(vault_resolved) + "/"):
        raise HTTPException(status_code=400, detail="Path outside vault")


@router.get("/panel")
async def tasks_panel(request: Request):
    config = request.app.state.config
    vault_path = config.tasks.vault_path
    if not vault_path or not vault_path.exists():
        return templates.TemplateResponse(request, "tasks.html", {"tasks": [], "groups": []})
    all_tasks = scan_tasks(vault_path)
    incomplete = [t for t in all_tasks if not t.completed]
    sorted_tasks = sorted(incomplete, key=lambda t: t.file.stem)
    groups = [(source, list(tasks)) for source, tasks in groupby(sorted_tasks, key=lambda t: t.file.stem)]
    return templates.TemplateResponse(request, "tasks.html", {"tasks": incomplete, "groups": groups})


@router.post("/toggle")
async def toggle(request: Request, file: str = Form(...), line: str = Form(...)):
    vault_path = request.app.state.config.tasks.vault_path
    _validate_vault_path(Path(file), vault_path)
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
