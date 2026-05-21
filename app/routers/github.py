import logging
from pathlib import Path

from fastapi import APIRouter, Form, Request
from app.config import build_github_repository, save_config
from app.templating import templates
from app.services.github import fetch_github_data

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/github")
CONFIG_PATH = Path("config.yaml")


@router.get("/panel")
async def github_panel(request: Request):
    orgs = request.app.state.config.github.orgs
    try:
        data = await fetch_github_data(orgs)
    except (OSError, ValueError) as e:
        logger.error("GitHub panel fetch failed: %s", e)
        return templates.TemplateResponse(
            request,
            "github.html",
            {
                "review_requests": [],
                "my_prs": [],
                "involved": [],
                "error": str(e),
            },
        )

    return templates.TemplateResponse(
        request,
        "github.html",
        {
            "review_requests": data.review_requests,
            "my_prs": data.my_prs,
            "involved": data.involved,
            "error": None,
        },
    )


@router.get("/repositories/panel")
async def repositories_panel(request: Request, error: str | None = None):
    return templates.TemplateResponse(
        request,
        "github_repositories.html",
        {
            "repositories": request.app.state.config.github.repositories,
            "error": error,
        },
    )


@router.post("/repositories/add")
async def add_repository(
    request: Request,
    repository: str = Form(...),
    display_name: str = Form(""),
):
    config = request.app.state.config
    try:
        shortcut = build_github_repository(repository, display_name)
    except ValueError as e:
        return await repositories_panel(request, str(e))

    config.github.repositories = [
        repo for repo in config.github.repositories if repo.url != shortcut.url
    ]
    config.github.repositories.append(shortcut)
    save_config(config, CONFIG_PATH)
    return await repositories_panel(request)


@router.post("/repositories/remove")
async def remove_repository(request: Request, url: str = Form(...)):
    config = request.app.state.config
    config.github.repositories = [
        repo for repo in config.github.repositories if repo.url != url
    ]
    save_config(config, CONFIG_PATH)
    return await repositories_panel(request)
