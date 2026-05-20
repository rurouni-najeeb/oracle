from fastapi import APIRouter, Request, Form
from app.templating import templates
from app.services.scratchpad import get_notes, add_note, update_note, delete_note

router = APIRouter(prefix="/scratchpad")


@router.get("/panel")
async def scratchpad_panel(request: Request):
    notes = get_notes()
    return templates.TemplateResponse(request, "scratchpad.html", {"notes": notes})


@router.post("/add")
async def add(request: Request, content: str = Form(...)):
    add_note(content)
    return await scratchpad_panel(request)


@router.post("/update")
async def update(request: Request, note_id: str = Form(...), content: str = Form(...)):
    update_note(note_id, content)
    return await scratchpad_panel(request)


@router.post("/delete")
async def delete(request: Request, note_id: str = Form(...)):
    delete_note(note_id)
    return await scratchpad_panel(request)
