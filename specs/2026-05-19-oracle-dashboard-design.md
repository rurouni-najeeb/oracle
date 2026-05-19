# Oracle — Personal Dashboard

## Overview

A local personal dashboard for tracking work and personal life. Combines Slack messages, Obsidian tasks, a Pomodoro timer, and RSS feeds in a single browser view.

Runs locally on macOS. Single-user, no auth in MVP (session management deferred to post-MVP).

## Tech Stack

- **Package management:** uv (pyproject.toml, public PyPI only)
- **Backend:** Python, FastAPI
- **Frontend:** Jinja2 templates + HTMX (minimal custom JS for the timer)
- **Slack:** MCP client calling the Slack MCP server
- **Tasks:** Direct filesystem read/write to Obsidian vault
- **RSS:** feedparser library with local cache
- **Config:** YAML file for user preferences (channels, feeds, vault path, timer durations)

## Architecture

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

Each panel is a FastAPI router that returns HTML fragments. HTMX swaps these fragments into the page on poll intervals or user actions.

## Project Structure

```
oracle/
├── config.yaml              # User config (channels, feeds, vault path, timer settings)
├── app/
│   ├── main.py              # FastAPI app setup, mount routers
│   ├── config.py            # Load/save config.yaml
│   ├── templates/
│   │   ├── base.html        # Page shell (head, HTMX script, grid layout)
│   │   ├── dashboard.html   # Main dashboard composing all panels
│   │   ├── slack.html       # Slack panel fragment
│   │   ├── tasks.html       # Tasks panel fragment
│   │   ├── pomodoro.html    # Pomodoro panel fragment
│   │   └── rss.html         # RSS panel fragment
│   ├── routers/
│   │   ├── slack.py         # Slack endpoints
│   │   ├── tasks.py         # Obsidian task endpoints
│   │   ├── pomodoro.py      # Timer endpoints
│   │   └── rss.py           # RSS feed endpoints
│   └── services/
│       ├── slack_mcp.py     # MCP client wrapper for Slack
│       ├── vault.py         # Obsidian vault reader/writer
│       ├── timer.py         # Pomodoro state machine
│       └── feeds.py         # RSS fetch + cache logic
├── static/
│   └── pomodoro.js          # Client-side countdown timer
├── pyproject.toml
└── specs/                   # Design docs
```

## Panel Specifications

### Slack Panel

**Purpose:** Surface important messages from selected channels without switching to Slack.

**Behavior:**
- Fetches recent messages from configured channels via Slack MCP (`slack_read_channel`)
- Displays messages with: channel name, author, timestamp, text
- HTMX polls every 30 seconds (`hx-trigger="every 30s"`)
- Unread indicator per channel (tracks last-seen timestamp locally)

**Configuration:**
- `config.yaml` contains a list of channel names to watch
- Settings UI allows adding/removing channels (writes back to config)

**Endpoints:**
- `GET /slack/panel` — returns full panel HTML fragment
- `GET /slack/messages/{channel}` — returns messages for one channel
- `POST /slack/channels` — add a channel to watch list
- `DELETE /slack/channels/{channel}` — remove a channel

### Tasks Panel (Obsidian)

**Purpose:** View and manage tasks from your Obsidian vault without opening Obsidian.

**Behavior:**
- Scans vault for lines matching `- [ ] ... #task` (incomplete) and `- [x] ... #task` (complete)
- Displays incomplete tasks grouped by source file (shows note title or date)
- Check off a task: writes `- [x]` back to the original file at the correct line
- Add task: appends `- [ ] <text> #task` to a configurable inbox file (default: today's daily note)
- No background polling — refreshes on user interaction

**Configuration:**
- `config.yaml` contains vault path and inbox file path

**Endpoints:**
- `GET /tasks/panel` — returns task list HTML fragment
- `POST /tasks/toggle` — toggle a task's completion state (params: file path, line number)
- `POST /tasks/add` — add a new task (params: text)

### Pomodoro Timer

**Purpose:** Focus timer with work/break cycles.

**Behavior:**
- Default: 25 min work, 5 min short break, 15 min long break (every 4 sessions)
- Client-side JS handles the visual countdown (avoids polling overhead)
- Server tracks: current phase, sessions completed today, timer running state
- Controls: start, pause, reset, skip to break/work
- Visual: circular progress indicator, phase label, session count

**Configuration:**
- `config.yaml` contains duration overrides (work_minutes, short_break, long_break)

**Endpoints:**
- `GET /pomodoro/panel` — returns timer HTML fragment with current state
- `POST /pomodoro/start` — start or resume timer
- `POST /pomodoro/pause` — pause timer
- `POST /pomodoro/reset` — reset current session
- `POST /pomodoro/skip` — skip to next phase
- `GET /pomodoro/state` — returns current state as JSON (for JS sync)

### RSS Panel

**Purpose:** Scroll through headlines and previews from your RSS feeds.

**Behavior:**
- Fetches configured RSS feeds using `feedparser`
- Caches feed data locally (refreshes every 5 minutes via HTMX poll)
- Displays: title, source, publication date, preview snippet (first ~150 chars)
- Click title opens article in new browser tab
- Mark-as-read state stored in a local JSON file

**Configuration:**
- `config.yaml` contains list of feed URLs with optional display names

**Endpoints:**
- `GET /rss/panel` — returns feed list HTML fragment
- `POST /rss/feeds` — add a feed URL
- `DELETE /rss/feeds/{feed_id}` — remove a feed
- `POST /rss/mark-read/{item_id}` — mark item as read

## Configuration File

```yaml
slack:
  channels:
    - general
    - engineering
    - alerts

tasks:
  vault_path: /Users/najeeb.khan/obsidian-vault
  inbox_file: daily  # "daily" = today's daily note (resolved to YYYY-MM-DD.md), or an explicit relative path like "inbox.md"

pomodoro:
  work_minutes: 25
  short_break_minutes: 5
  long_break_minutes: 15
  sessions_before_long_break: 4

rss:
  feeds:
    - url: https://example.com/feed.xml
      name: Example Blog
    - url: https://another.com/rss
      name: Another Feed
  refresh_interval_minutes: 5
```

## Data Flow

**Slack:** FastAPI → MCP client → Slack MCP server → Slack API → messages returned → rendered as HTML fragment → HTMX swaps into panel

**Tasks:** FastAPI → reads vault files from disk → parses checkboxes with #task tag → renders as HTML → on toggle, writes back to the specific file and line

**Pomodoro:** Page loads → JS starts countdown from server state → on phase change, JS calls server to update state → server tracks sessions

**RSS:** FastAPI → feedparser fetches URLs → caches parsed entries → renders as HTML fragment → HTMX polls for refresh

## Error Handling

- Slack MCP unreachable: panel shows "Unable to reach Slack — check MCP server" with retry button
- Vault path invalid: tasks panel shows config error with link to settings
- RSS feed fails: skip that feed, show others; indicate which feeds errored
- All errors are non-fatal — other panels continue working

## Future (Post-MVP)

- Login/logout with session management
- Dashboard layout customization (drag/resize panels)
- Browser notifications for Pomodoro phase changes
- Slack thread expansion
- Task filtering/sorting by tags or due dates
