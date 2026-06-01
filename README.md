# Oracle

A personal dashboard for macOS that surfaces your calendar, GitHub PRs, tasks, RSS feeds, notes, and a pomodoro timer in one window.

![macOS](https://img.shields.io/badge/platform-macOS-lightgrey)
![Python](https://img.shields.io/badge/python-3.12%2B-blue)

## Features

- **Calendar** — Shows today's and tomorrow's events from macOS Calendar.app
- **GitHub** — Open PRs, review requests, PRs you've commented on, and pinned repository shortcuts
- **Tasks** — Obsidian vault task integration (read/toggle/add tasks from markdown files)
- **RSS** — Feed reader with add/remove management and read/unread tracking
- **Scratchpad** — Quick notes with create, edit, and delete
- **Pomodoro** — Configurable timer with work/short break/long break phases

All state (pomodoro progress, read articles, notes) persists in a local SQLite database at `~/.oracle/oracle.db`.

## Prerequisites

- macOS 12+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [gh](https://cli.github.com/) (GitHub CLI, authenticated)
- Access to macOS Calendar.app (for calendar events)
- An [Obsidian](https://obsidian.md/) vault (for tasks, optional)

## Setup

```bash
# Clone the repo
git clone <repo-url>
cd oracle

# Install dependencies
uv sync

# Create your config
cp config.yaml.example config.yaml
# Edit config.yaml with your vault path, GitHub orgs, and feeds
```

## Running

### As a desktop app (recommended)

```bash
uv run python desktop.py
```

This opens Oracle in a native macOS window (WebKit). The app also lives at `/Applications/Oracle.app` if the symlink was created — searchable via Spotlight.

### As a web server (development)

```bash
uv run uvicorn app.main:app --reload --port 8000
```

Then open `http://localhost:8000` in a browser.

### Using Taskfile

```bash
task dev      # Start dev server with auto-reload
task test     # Run tests
task lint     # Run ruff linter
task format   # Format code
task check    # Lint + tests
```

## Configuration

Copy the example config and edit it:

```bash
cp config.yaml.example config.yaml
```

```yaml
tasks:
  vault_path: /path/to/your/obsidian/vault
  inbox_file: daily  # File to add new tasks to

pomodoro:
  work_minutes: 25
  short_break_minutes: 5
  long_break_minutes: 15
  sessions_before_long_break: 4

rss:
  feeds:
    - name: Ars Technica
      url: https://feeds.arstechnica.com/arstechnica/technology-lab
    - name: Hacker News
      url: https://hnrss.org/frontpage
  refresh_interval_minutes: 5

github:
  orgs:
    - my-github-org
    - another-org
  repositories:
    - owner: my-github-org
      repo: oracle
      display_name: Oracle
      url: https://github.com/my-github-org/oracle
```

RSS feeds can also be added and removed directly from the panel UI.

## Architecture

```
oracle/
├── app/
│   ├── main.py              # FastAPI app setup, mounts routers
│   ├── config.py            # YAML config loading/saving
│   ├── db.py                # SQLite init and connection
│   ├── templating.py        # Shared Jinja2 templates instance
│   ├── routers/             # HTTP endpoints per panel
│   │   ├── dashboard.py     # Main page (renders all panels)
│   │   ├── calendar.py
│   │   ├── github.py
│   │   ├── tasks.py
│   │   ├── pomodoro.py
│   │   ├── rss.py
│   │   └── scratchpad.py
│   ├── services/            # Business logic
│   │   ├── calendar.py      # JXA → Calendar.app events
│   │   ├── github.py        # gh CLI → PR data
│   │   ├── feeds.py         # feedparser + caching
│   │   ├── scratchpad.py    # Notes CRUD
│   │   ├── timer.py         # Pomodoro state machine
│   │   └── vault.py         # Obsidian vault task scanner
│   └── templates/           # Jinja2 HTML fragments
├── static/
│   ├── style.css
│   └── pomodoro.js
├── tests/
├── desktop.py               # pywebview launcher
├── Oracle.app/              # macOS app bundle
├── config.yaml
├── Taskfile.yml
└── pyproject.toml
```

### Tech Stack

- **Backend:** FastAPI + Uvicorn
- **Frontend:** Jinja2 templates + HTMX (server-rendered HTML fragments)
- **Desktop:** pywebview (native WebKit window)
- **Database:** SQLite (WAL mode)
- **Calendar:** JXA (JavaScript for Automation) via `osascript`
- **GitHub:** `gh` CLI
- **RSS:** feedparser

### Panel Refresh

Each panel polls independently via HTMX:

| Panel | Interval | Source |
|-------|----------|--------|
| Calendar | 60s | macOS Calendar.app |
| GitHub | 120s | GitHub API via `gh` |
| Repositories | on interaction | Local config |
| RSS | 300s | feedparser |
| Pomodoro | client-side | JS timer + server sync |
| Tasks | on interaction | Obsidian vault files |
| Scratchpad | on interaction | SQLite |

## Database

State is stored in `~/.oracle/oracle.db` (created automatically on first run):

- `notes` — Scratchpad entries
- `read_items` — RSS read/unread tracking
- `pomodoro_state` — Timer phase, remaining time, sessions count

## Tests

```bash
uv run pytest -v
```

Tests are isolated from the production database using temporary SQLite instances.

## Installing as a macOS App

To make Oracle launchable from Spotlight:

```bash
# Create the app bundle (one-time setup)
ln -sf "$(pwd)/Oracle.app" /Applications/Oracle.app
```

The app bundle uses relative paths, so it works from wherever the repo is cloned.

## License

MIT
