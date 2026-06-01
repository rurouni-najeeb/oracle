# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync

# Dev server (http://localhost:8000)
uv run uvicorn app.main:app --reload --port 8000

# Desktop app (native macOS WebKit window)
uv run python desktop.py

# Tests
uv run pytest -v              # all tests
uv run pytest tests/test_config.py -v   # single file
uv run pytest -k "test_name" -v         # single test by name

# Lint & format
uv run ruff check .
uv run ruff format .

# Taskfile shortcuts (requires `task` CLI)
task dev    # dev server
task test   # tests
task check  # lint + tests
```

## Workflow

- Every change should result in a PR to `main`.
- When enough features have accumulated, create a GitHub release.

## Architecture

Oracle is a personal macOS dashboard. FastAPI serves HTML fragments via HTMX — there is no client-side framework or SPA routing. Each panel is an independent HTML fragment loaded into the dashboard grid.

### Request flow

1. `dashboard.html` renders a grid of `<section>` elements, each with an `hx-get` that loads its panel fragment on page load
2. Panel routers (`app/routers/`) return rendered Jinja2 template fragments (not full pages)
3. HTMX swaps the fragment into the panel's container — no full page reloads
4. Mutations (add/edit/delete) POST to the router and return the full panel fragment to re-render

### Key patterns

- **Router → Service → DB**: Routers handle HTTP, services contain business logic, `app/db.py` provides a `get_db()` context manager for SQLite connections.
- **Config**: `config.yaml` is loaded once at startup into `app.state.config` (dataclass tree in `app/config.py`). RSS feeds can also be mutated at runtime via `save_config()`.
- **Templating**: `app/templating.py` exposes a shared `templates` instance with an `|md` filter for inline markdown rendering (sanitized with nh3).
- **Desktop**: `desktop.py` starts uvicorn in a daemon thread and opens a pywebview window pointing at it. The same HTML/CSS/JS runs in both browser and native window.

### Database

SQLite at `~/.oracle/oracle.db` with WAL mode. Schema is created in `app/db.py:init_db()` which runs at import time of `app.main`. Tables: `notes`, `read_items`, `pomodoro_state`.

### External dependencies

- **Calendar**: calls `osascript` with JXA to read macOS Calendar.app events
- **GitHub**: shells out to `gh` CLI (must be authenticated)
- **RSS**: uses `feedparser` with an in-memory TTL cache (`FeedService`)
- **Tasks**: reads/writes markdown files in an Obsidian vault directory
