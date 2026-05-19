import json
import subprocess
from dataclasses import dataclass


@dataclass
class SlackMessage:
    channel: str
    author: str
    text: str
    timestamp: str


class SlackMCPClient:
    """Calls the Slack MCP server's tools via stdio transport."""

    def __init__(self, server_command: list[str] | None = None):
        self._server_command = server_command or ["npx", "@anthropic/slack-mcp"]

    async def read_channel(self, channel: str, limit: int = 20) -> list[SlackMessage]:
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "slack_read_channel",
                "arguments": {"channel_name": channel, "limit": limit},
            },
        }
        try:
            proc = subprocess.run(
                self._server_command,
                input=json.dumps(request),
                capture_output=True,
                text=True,
                timeout=30,
            )
            response = json.loads(proc.stdout)
            content = response.get("result", {}).get("content", [])
            messages = []
            for item in content:
                if item.get("type") == "text":
                    messages.append(SlackMessage(
                        channel=channel,
                        author=item.get("author", "unknown"),
                        text=item.get("text", ""),
                        timestamp=item.get("timestamp", ""),
                    ))
            return messages
        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
            return []
