# Oracle Dashboard — Architecture

## System Diagram

```
┌─────────────────────────────────────────────────┐
│                  Browser (HTMX)                  │
│  ┌──────────┬──────────┬──────────┬──────────┐  │
│  │  Slack   │  Tasks   │ Pomodoro │   RSS    │  │
│  │  Panel   │  Panel   │  Timer   │  Panel   │  │
│  └──────────┴──────────┴──────────┴──────────┘  │
└────────────────────┬────────────────────────────┘
                     │ HTTP (HTMX polls/triggers)
┌────────────────────▼────────────────────────────┐
│              FastAPI Server                       │
│  ┌──────────┬──────────┬──────────┬──────────┐  │
│  │  Slack   │ Obsidian │Pomodoro  │   RSS    │  │
│  │  Router  │  Router  │ Router   │  Router  │  │
│  └────┬─────┴────┬─────┴──────────┴────┬─────┘  │
│       │          │                      │        │
│  ┌────▼───┐ ┌───▼────┐           ┌────▼─────┐  │
│  │  MCP   │ │  Vault │           │ feedparser│  │
│  │ Client │ │ Reader │           │           │  │
│  └────┬───┘ └───┬────┘           └──────────┘  │
└───────┼─────────┼───────────────────────────────┘
        │         │
   Slack MCP   Obsidian
   Server      Vault (fs)
```

## Key Decisions

- Each panel is a FastAPI router serving HTML fragments
- HTMX handles polling (Slack messages every 30s, RSS every 5min) and user interactions
- Pomodoro timer runs client-side (a small JS countdown) with server tracking state (start/pause/reset)
- Obsidian integration reads/writes markdown files directly on disk
- Slack integration calls the Slack MCP server as a client
- Config (channel list, RSS feeds, vault path) stored in a local JSON/YAML file
