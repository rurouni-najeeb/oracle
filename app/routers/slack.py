from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.services.slack_mcp import SlackMCPClient

router = APIRouter(prefix="/slack")
templates = Jinja2Templates(directory="app/templates")

_client: SlackMCPClient | None = None


def _get_client() -> SlackMCPClient:
    global _client
    if _client is None:
        _client = SlackMCPClient()
    return _client


@router.get("/panel")
async def slack_panel(request: Request):
    config = request.app.state.config
    channels = config.slack.channels
    client = _get_client()

    all_messages = []
    error = None
    for channel in channels:
        try:
            messages = await client.read_channel(channel, limit=10)
            all_messages.extend(messages)
        except Exception as e:
            error = f"Unable to reach Slack MCP server: {e}"
            break

    all_messages.sort(key=lambda m: m.timestamp, reverse=True)
    return templates.TemplateResponse(request, "slack.html", {
        "messages": all_messages,
        "error": error,
    })
