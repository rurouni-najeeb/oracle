import logging

from fastapi import APIRouter, Request
from app.templating import templates
from app.services.github import fetch_github_data

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/github")

ORGS = ["moia-dev", "moia-oss", "moia-playground"]


@router.get("/panel")
async def github_panel(request: Request):
    try:
        data = await fetch_github_data(ORGS)
    except (OSError, ValueError) as e:
        logger.error("GitHub panel fetch failed: %s", e)
        return templates.TemplateResponse(request, "github.html", {
            "review_requests": [],
            "my_prs": [],
            "commented": [],
            "error": str(e),
        })

    return templates.TemplateResponse(request, "github.html", {
        "review_requests": data.review_requests,
        "my_prs": data.my_prs,
        "commented": data.commented,
        "error": None,
    })
