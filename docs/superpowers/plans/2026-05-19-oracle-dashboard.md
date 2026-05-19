# Oracle Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local personal dashboard combining Slack messages, Obsidian tasks, a Pomodoro timer, and RSS feeds in one browser view.

**Architecture:** FastAPI backend serving Jinja2 HTML fragments, with HTMX handling dynamic updates (polling, form submissions). Each panel is an independent router + service pair. Config stored in YAML.

**Tech Stack:** Python 3.12+, FastAPI, Jinja2, HTMX, uv (package management), feedparser, PyYAML, httpx

---

## File Structure

```
oracle/
├── pyproject.toml               # Project metadata + dependencies
├── config.yaml                  # User configuration (channels, feeds, vault path)
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app creation, router mounting, static files
│   ├── config.py                # Load/save config.yaml, typed config model
│   ├── templates/
│   │   ├── base.html            # Page shell: <head>, HTMX CDN, CSS grid layout
│   │   ├── dashboard.html       # Extends base, includes all panel fragments
│   │   ├── slack.html           # Slack panel fragment
│   │   ├── tasks.html           # Tasks panel fragment
│   │   ├── pomodoro.html        # Pomodoro panel fragment
│   │   └── rss.html             # RSS panel fragment
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── dashboard.py         # GET / → renders dashboard.html
│   │   ├── slack.py             # Slack panel endpoints
│   │   ├── tasks.py             # Tasks panel endpoints
│   │   ├── pomodoro.py          # Pomodoro panel endpoints
│   │   └── rss.py               # RSS panel endpoints
│   └── services/
│       ├── __init__.py
│       ├── slack_mcp.py         # MCP client wrapper for Slack reads
│       ├── vault.py             # Obsidian vault scanner/writer
│       ├── timer.py             # Pomodoro state machine (in-memory)
│       └── feeds.py             # RSS fetch + cache
├── static/
│   ├── style.css                # Dashboard styles
│   └── pomodoro.js              # Client-side countdown
└── tests/
    ├── __init__.py
    ├── conftest.py              # Shared fixtures (test client, tmp vault, tmp config)
    ├── test_config.py           # Config loading tests
    ├── test_vault.py            # Obsidian vault service tests
    ├── test_timer.py            # Pomodoro state machine tests
    ├── test_feeds.py            # RSS feed service tests
    ├── test_tasks_router.py     # Tasks router integration tests
    ├── test_pomodoro_router.py  # Pomodoro router integration tests
    └── test_rss_router.py       # RSS router integration tests
```

---

## Task 1: Project Scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `config.yaml`
- Create: `app/__init__.py`
- Create: `app/main.py`
- Create: `app/config.py`
- Create: `app/templates/base.html`
- Create: `app/templates/dashboard.html`
- Create: `app/routers/__init__.py`
- Create: `app/routers/dashboard.py`
- Create: `app/services/__init__.py`
- Create: `static/style.css`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Initialize project with uv**

```bash
cd /Users/najeeb.khan/oracle
uv init --no-readme
```

- [ ] **Step 2: Edit pyproject.toml with dependencies**

```toml
[project]
name = "oracle"
version = "0.1.0"
description = "Personal dashboard"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "jinja2>=3.1.0",
    "pyyaml>=6.0",
    "httpx>=0.27.0",
    "feedparser>=6.0",
]

[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "httpx>=0.27.0",
]
```

- [ ] **Step 3: Install dependencies**

```bash
uv sync
```

- [ ] **Step 4: Create config.yaml**

```yaml
slack:
  channels:
    - general

tasks:
  vault_path: ""
  inbox_file: daily

pomodoro:
  work_minutes: 25
  short_break_minutes: 5
  long_break_minutes: 15
  sessions_before_long_break: 4

rss:
  feeds: []
  refresh_interval_minutes: 5
```

- [ ] **Step 5: Write the failing test for config loading**

Create `tests/__init__.py` (empty) and `tests/test_config.py`:

```python
import pytest
from pathlib import Path
from app.config import load_config, AppConfig


def test_load_config_from_file(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("""
slack:
  channels:
    - general
    - alerts
tasks:
  vault_path: /tmp/vault
  inbox_file: daily
pomodoro:
  work_minutes: 25
  short_break_minutes: 5
  long_break_minutes: 15
  sessions_before_long_break: 4
rss:
  feeds:
    - url: https://example.com/feed.xml
      name: Example
  refresh_interval_minutes: 5
""")
    config = load_config(config_file)
    assert isinstance(config, AppConfig)
    assert config.slack.channels == ["general", "alerts"]
    assert config.tasks.vault_path == Path("/tmp/vault")
    assert config.rss.feeds[0].url == "https://example.com/feed.xml"
    assert config.pomodoro.work_minutes == 25
```

- [ ] **Step 6: Run test to verify it fails**

```bash
uv run pytest tests/test_config.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'app'`

- [ ] **Step 7: Implement config module**

Create `app/__init__.py` (empty) and `app/config.py`:

```python
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import yaml


@dataclass
class SlackConfig:
    channels: list[str] = field(default_factory=list)


@dataclass
class TasksConfig:
    vault_path: Path = Path("")
    inbox_file: str = "daily"


@dataclass
class PomodoroConfig:
    work_minutes: int = 25
    short_break_minutes: int = 5
    long_break_minutes: int = 15
    sessions_before_long_break: int = 4


@dataclass
class FeedEntry:
    url: str = ""
    name: str = ""


@dataclass
class RSSConfig:
    feeds: list[FeedEntry] = field(default_factory=list)
    refresh_interval_minutes: int = 5


@dataclass
class AppConfig:
    slack: SlackConfig = field(default_factory=SlackConfig)
    tasks: TasksConfig = field(default_factory=TasksConfig)
    pomodoro: PomodoroConfig = field(default_factory=PomodoroConfig)
    rss: RSSConfig = field(default_factory=RSSConfig)


def load_config(path: Path) -> AppConfig:
    with open(path) as f:
        data = yaml.safe_load(f) or {}

    slack = SlackConfig(channels=data.get("slack", {}).get("channels", []))

    tasks_data = data.get("tasks", {})
    tasks = TasksConfig(
        vault_path=Path(tasks_data.get("vault_path", "")),
        inbox_file=tasks_data.get("inbox_file", "daily"),
    )

    pomo_data = data.get("pomodoro", {})
    pomodoro = PomodoroConfig(
        work_minutes=pomo_data.get("work_minutes", 25),
        short_break_minutes=pomo_data.get("short_break_minutes", 5),
        long_break_minutes=pomo_data.get("long_break_minutes", 15),
        sessions_before_long_break=pomo_data.get("sessions_before_long_break", 4),
    )

    rss_data = data.get("rss", {})
    feeds = [FeedEntry(url=f.get("url", ""), name=f.get("name", "")) for f in rss_data.get("feeds", [])]
    rss = RSSConfig(feeds=feeds, refresh_interval_minutes=rss_data.get("refresh_interval_minutes", 5))

    return AppConfig(slack=slack, tasks=tasks, pomodoro=pomodoro, rss=rss)


def save_config(config: AppConfig, path: Path) -> None:
    data = {
        "slack": {"channels": config.slack.channels},
        "tasks": {
            "vault_path": str(config.tasks.vault_path),
            "inbox_file": config.tasks.inbox_file,
        },
        "pomodoro": {
            "work_minutes": config.pomodoro.work_minutes,
            "short_break_minutes": config.pomodoro.short_break_minutes,
            "long_break_minutes": config.pomodoro.long_break_minutes,
            "sessions_before_long_break": config.pomodoro.sessions_before_long_break,
        },
        "rss": {
            "feeds": [{"url": f.url, "name": f.name} for f in config.rss.feeds],
            "refresh_interval_minutes": config.rss.refresh_interval_minutes,
        },
    }
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False)
```

- [ ] **Step 8: Run test to verify it passes**

```bash
uv run pytest tests/test_config.py -v
```

Expected: PASS

- [ ] **Step 9: Create base template**

Create `app/templates/base.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Oracle Dashboard</title>
    <script src="https://unpkg.com/htmx.org@2.0.4"></script>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <header>
        <h1>Oracle</h1>
    </header>
    <main class="dashboard-grid">
        {% block content %}{% endblock %}
    </main>
    {% block scripts %}{% endblock %}
</body>
</html>
```

- [ ] **Step 10: Create dashboard template**

Create `app/templates/dashboard.html`:

```html
{% extends "base.html" %}
{% block content %}
<section class="panel" id="slack-panel">
    <div hx-get="/slack/panel" hx-trigger="load, every 30s" hx-swap="innerHTML">
        <p>Loading Slack messages...</p>
    </div>
</section>

<section class="panel" id="tasks-panel">
    <div hx-get="/tasks/panel" hx-trigger="load" hx-swap="innerHTML">
        <p>Loading tasks...</p>
    </div>
</section>

<section class="panel" id="pomodoro-panel">
    <div hx-get="/pomodoro/panel" hx-trigger="load" hx-swap="innerHTML">
        <p>Loading timer...</p>
    </div>
</section>

<section class="panel" id="rss-panel">
    <div hx-get="/rss/panel" hx-trigger="load, every 300s" hx-swap="innerHTML">
        <p>Loading feeds...</p>
    </div>
</section>
{% endblock %}

{% block scripts %}
<script src="/static/pomodoro.js"></script>
{% endblock %}
```

- [ ] **Step 11: Create basic CSS**

Create `static/style.css`:

```css
* { margin: 0; padding: 0; box-sizing: border-box; }

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: #1a1a2e;
    color: #e0e0e0;
    min-height: 100vh;
}

header {
    padding: 1rem 2rem;
    background: #16213e;
    border-bottom: 1px solid #0f3460;
}

header h1 {
    font-size: 1.5rem;
    color: #e94560;
}

.dashboard-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-template-rows: 1fr 1fr;
    gap: 1rem;
    padding: 1rem;
    height: calc(100vh - 4rem);
}

.panel {
    background: #16213e;
    border: 1px solid #0f3460;
    border-radius: 8px;
    padding: 1rem;
    overflow-y: auto;
}

.panel h2 {
    font-size: 1.1rem;
    margin-bottom: 0.75rem;
    color: #e94560;
    border-bottom: 1px solid #0f3460;
    padding-bottom: 0.5rem;
}
```

- [ ] **Step 12: Create dashboard router**

Create `app/routers/__init__.py` (empty) and `app/routers/dashboard.py`:

```python
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})
```

- [ ] **Step 13: Create FastAPI app**

Create `app/main.py`:

```python
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.config import load_config, AppConfig
from app.routers import dashboard

CONFIG_PATH = Path("config.yaml")

app = FastAPI(title="Oracle Dashboard")
app.mount("/static", StaticFiles(directory="static"), name="static")

app.state.config = load_config(CONFIG_PATH)

app.include_router(dashboard.router)
```

- [ ] **Step 14: Create test conftest**

Create `tests/conftest.py`:

```python
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def tmp_vault(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    return vault


@pytest.fixture
def sample_config(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("""
slack:
  channels: [general]
tasks:
  vault_path: ""
  inbox_file: daily
pomodoro:
  work_minutes: 25
  short_break_minutes: 5
  long_break_minutes: 15
  sessions_before_long_break: 4
rss:
  feeds: []
  refresh_interval_minutes: 5
""")
    return config_file
```

- [ ] **Step 15: Verify the app starts**

```bash
uv run uvicorn app.main:app --port 8000 &
sleep 2
curl -s http://localhost:8000 | head -5
kill %1
```

Expected: HTML containing "Oracle" in the title

- [ ] **Step 16: Commit**

```bash
git init
echo ".superpowers/" >> .gitignore
echo "__pycache__/" >> .gitignore
echo ".venv/" >> .gitignore
git add .
git commit -m "feat: project scaffold with config, templates, and dashboard shell"
```

---

## Task 2: Obsidian Tasks Service

**Files:**
- Create: `app/services/__init__.py`
- Create: `app/services/vault.py`
- Create: `tests/test_vault.py`

- [ ] **Step 1: Write failing tests for vault scanner**

Create `app/services/__init__.py` (empty) and `tests/test_vault.py`:

```python
import pytest
from pathlib import Path
from app.services.vault import scan_tasks, toggle_task, add_task, Task


def test_scan_finds_incomplete_tasks(tmp_path):
    note = tmp_path / "2026-05-19.md"
    note.write_text("# Today\n- [ ] Buy groceries #task\n- [x] Call dentist #task\n- Regular note\n")
    tasks = scan_tasks(tmp_path)
    incomplete = [t for t in tasks if not t.completed]
    assert len(incomplete) == 1
    assert incomplete[0].text == "Buy groceries"
    assert incomplete[0].file == note
    assert incomplete[0].line == 2


def test_scan_finds_tasks_across_files(tmp_path):
    (tmp_path / "a.md").write_text("- [ ] Task A #task\n")
    (tmp_path / "b.md").write_text("- [ ] Task B #task\n")
    tasks = scan_tasks(tmp_path)
    incomplete = [t for t in tasks if not t.completed]
    assert len(incomplete) == 2


def test_scan_ignores_non_task_checkboxes(tmp_path):
    note = tmp_path / "note.md"
    note.write_text("- [ ] Not a task\n- [ ] Is a task #task\n")
    tasks = scan_tasks(tmp_path)
    assert len(tasks) == 1
    assert tasks[0].text == "Is a task"


def test_toggle_task_completes(tmp_path):
    note = tmp_path / "note.md"
    note.write_text("- [ ] Do thing #task\n")
    toggle_task(note, line=1)
    content = note.read_text()
    assert "- [x] Do thing #task" in content


def test_toggle_task_uncompletes(tmp_path):
    note = tmp_path / "note.md"
    note.write_text("- [x] Done thing #task\n")
    toggle_task(note, line=1)
    content = note.read_text()
    assert "- [ ] Done thing #task" in content


def test_add_task_to_file(tmp_path):
    note = tmp_path / "inbox.md"
    note.write_text("# Inbox\n")
    add_task(note, "New task")
    content = note.read_text()
    assert "- [ ] New task #task" in content


def test_add_task_creates_file_if_missing(tmp_path):
    note = tmp_path / "2026-05-19.md"
    add_task(note, "First task")
    assert note.exists()
    content = note.read_text()
    assert "- [ ] First task #task" in content
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_vault.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.vault'`

- [ ] **Step 3: Implement vault service**

Create `app/services/vault.py`:

```python
import re
from dataclasses import dataclass
from pathlib import Path

TASK_PATTERN = re.compile(r"^- \[([ x])\] (.+?)(?:\s+#task)\s*$")


@dataclass
class Task:
    text: str
    completed: bool
    file: Path
    line: int


def scan_tasks(vault_path: Path) -> list[Task]:
    tasks = []
    for md_file in sorted(vault_path.rglob("*.md")):
        lines = md_file.read_text().splitlines()
        for i, line in enumerate(lines, start=1):
            match = TASK_PATTERN.match(line)
            if match:
                completed = match.group(1) == "x"
                text = match.group(2).strip()
                tasks.append(Task(text=text, completed=completed, file=md_file, line=i))
    return tasks


def toggle_task(file: Path, line: int) -> None:
    lines = file.read_text().splitlines()
    idx = line - 1
    if idx < 0 or idx >= len(lines):
        return
    if "- [ ]" in lines[idx]:
        lines[idx] = lines[idx].replace("- [ ]", "- [x]", 1)
    elif "- [x]" in lines[idx]:
        lines[idx] = lines[idx].replace("- [x]", "- [ ]", 1)
    file.write_text("\n".join(lines) + "\n")


def add_task(file: Path, text: str) -> None:
    if file.exists():
        content = file.read_text()
        if not content.endswith("\n"):
            content += "\n"
        content += f"- [ ] {text} #task\n"
    else:
        content = f"- [ ] {text} #task\n"
    file.write_text(content)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_vault.py -v
```

Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add app/services/ tests/test_vault.py
git commit -m "feat: obsidian vault service — scan, toggle, and add tasks"
```

---

## Task 3: Tasks Router

**Files:**
- Create: `app/routers/tasks.py`
- Create: `app/templates/tasks.html`
- Create: `tests/test_tasks_router.py`

- [ ] **Step 1: Write failing tests for tasks router**

Create `tests/test_tasks_router.py`:

```python
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client_with_vault(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "note.md").write_text("- [ ] Test task #task\n- [x] Done task #task\n")
    app.state.config.tasks.vault_path = vault
    app.state.config.tasks.inbox_file = "inbox.md"
    return TestClient(app)


def test_tasks_panel_returns_html(client_with_vault):
    response = client_with_vault.get("/tasks/panel")
    assert response.status_code == 200
    assert "Test task" in response.text
    assert "text/html" in response.headers["content-type"]


def test_toggle_task(client_with_vault, tmp_path):
    vault = tmp_path / "vault"
    response = client_with_vault.post(
        "/tasks/toggle",
        data={"file": str(vault / "note.md"), "line": "1"},
    )
    assert response.status_code == 200
    content = (vault / "note.md").read_text()
    assert "- [x] Test task #task" in content


def test_add_task(client_with_vault, tmp_path):
    vault = tmp_path / "vault"
    response = client_with_vault.post(
        "/tasks/add",
        data={"text": "New task from dashboard"},
    )
    assert response.status_code == 200
    inbox = vault / "inbox.md"
    assert inbox.exists()
    assert "New task from dashboard" in inbox.read_text()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_tasks_router.py -v
```

Expected: FAIL — router not registered / 404

- [ ] **Step 3: Create tasks template**

Create `app/templates/tasks.html`:

```html
<h2>Tasks</h2>

<form hx-post="/tasks/add" hx-target="#tasks-panel > div" hx-swap="innerHTML" class="add-task-form">
    <input type="text" name="text" placeholder="Add a task..." required>
    <button type="submit">+</button>
</form>

{% if tasks %}
<ul class="task-list">
    {% for task in tasks %}
    <li class="task-item {% if task.completed %}completed{% endif %}">
        <form hx-post="/tasks/toggle" hx-target="#tasks-panel > div" hx-swap="innerHTML">
            <input type="hidden" name="file" value="{{ task.file }}">
            <input type="hidden" name="line" value="{{ task.line }}">
            <button type="submit" class="checkbox">
                {% if task.completed %}[x]{% else %}[ ]{% endif %}
            </button>
        </form>
        <span class="task-text">{{ task.text }}</span>
        <span class="task-source">{{ task.file.stem }}</span>
    </li>
    {% endfor %}
</ul>
{% else %}
<p class="empty-state">No tasks found.</p>
{% endif %}
```

- [ ] **Step 4: Implement tasks router**

Create `app/routers/tasks.py`:

```python
from datetime import date
from pathlib import Path
from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from app.services.vault import scan_tasks, toggle_task, add_task

router = APIRouter(prefix="/tasks")
templates = Jinja2Templates(directory="app/templates")


@router.get("/panel")
async def tasks_panel(request: Request):
    config = request.app.state.config
    vault_path = config.tasks.vault_path
    if not vault_path or not vault_path.exists():
        return templates.TemplateResponse("tasks.html", {"request": request, "tasks": [], "error": "Vault path not configured"})
    all_tasks = scan_tasks(vault_path)
    incomplete = [t for t in all_tasks if not t.completed]
    return templates.TemplateResponse("tasks.html", {"request": request, "tasks": incomplete})


@router.post("/toggle")
async def toggle(request: Request, file: str = Form(...), line: str = Form(...)):
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
```

- [ ] **Step 5: Register router in main.py**

Add to `app/main.py`:

```python
from app.routers import dashboard, tasks

# ... after existing router include
app.include_router(tasks.router)
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
uv run pytest tests/test_tasks_router.py -v
```

Expected: All PASS

- [ ] **Step 7: Commit**

```bash
git add app/routers/tasks.py app/templates/tasks.html app/main.py tests/test_tasks_router.py
git commit -m "feat: tasks panel — display, toggle, and add obsidian tasks"
```

---

## Task 4: Pomodoro Timer Service

**Files:**
- Create: `app/services/timer.py`
- Create: `tests/test_timer.py`

- [ ] **Step 1: Write failing tests for timer state machine**

Create `tests/test_timer.py`:

```python
import pytest
from app.services.timer import PomodoroTimer, Phase


def test_initial_state():
    timer = PomodoroTimer(work_minutes=25, short_break=5, long_break=15, long_break_interval=4)
    assert timer.phase == Phase.WORK
    assert timer.remaining_seconds == 25 * 60
    assert timer.running is False
    assert timer.sessions_completed == 0


def test_start():
    timer = PomodoroTimer(work_minutes=25, short_break=5, long_break=15, long_break_interval=4)
    timer.start()
    assert timer.running is True


def test_pause():
    timer = PomodoroTimer(work_minutes=25, short_break=5, long_break=15, long_break_interval=4)
    timer.start()
    timer.pause()
    assert timer.running is False


def test_reset():
    timer = PomodoroTimer(work_minutes=25, short_break=5, long_break=15, long_break_interval=4)
    timer.start()
    timer.remaining_seconds = 100
    timer.reset()
    assert timer.remaining_seconds == 25 * 60
    assert timer.running is False


def test_skip_from_work_to_short_break():
    timer = PomodoroTimer(work_minutes=25, short_break=5, long_break=15, long_break_interval=4)
    timer.skip()
    assert timer.phase == Phase.SHORT_BREAK
    assert timer.remaining_seconds == 5 * 60
    assert timer.sessions_completed == 1


def test_skip_from_break_to_work():
    timer = PomodoroTimer(work_minutes=25, short_break=5, long_break=15, long_break_interval=4)
    timer.skip()  # work -> short break
    timer.skip()  # short break -> work
    assert timer.phase == Phase.WORK
    assert timer.remaining_seconds == 25 * 60


def test_long_break_after_interval():
    timer = PomodoroTimer(work_minutes=25, short_break=5, long_break=15, long_break_interval=4)
    for _ in range(4):
        timer.skip()  # work -> break
        timer.skip()  # break -> work
    # After 4 work sessions completed, next skip should give long break
    # Actually session 4 just completed on the 4th skip-from-work
    # Let's re-check: skip from work increments sessions
    timer2 = PomodoroTimer(work_minutes=25, short_break=5, long_break=15, long_break_interval=4)
    for i in range(3):
        timer2.skip()  # work -> short break (sessions: i+1)
        timer2.skip()  # break -> work
    timer2.skip()  # 4th work -> should be long break
    assert timer2.phase == Phase.LONG_BREAK
    assert timer2.remaining_seconds == 15 * 60
    assert timer2.sessions_completed == 4


def test_get_state():
    timer = PomodoroTimer(work_minutes=25, short_break=5, long_break=15, long_break_interval=4)
    state = timer.get_state()
    assert state["phase"] == "work"
    assert state["remaining_seconds"] == 1500
    assert state["running"] is False
    assert state["sessions_completed"] == 0
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_timer.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement timer service**

Create `app/services/timer.py`:

```python
from enum import Enum


class Phase(str, Enum):
    WORK = "work"
    SHORT_BREAK = "short_break"
    LONG_BREAK = "long_break"


class PomodoroTimer:
    def __init__(self, work_minutes: int, short_break: int, long_break: int, long_break_interval: int):
        self.work_minutes = work_minutes
        self.short_break = short_break
        self.long_break = long_break
        self.long_break_interval = long_break_interval
        self.phase = Phase.WORK
        self.remaining_seconds = work_minutes * 60
        self.running = False
        self.sessions_completed = 0

    def start(self) -> None:
        self.running = True

    def pause(self) -> None:
        self.running = False

    def reset(self) -> None:
        self.running = False
        self.remaining_seconds = self._duration_for_phase(self.phase)

    def skip(self) -> None:
        if self.phase == Phase.WORK:
            self.sessions_completed += 1
            if self.sessions_completed % self.long_break_interval == 0:
                self.phase = Phase.LONG_BREAK
            else:
                self.phase = Phase.SHORT_BREAK
        else:
            self.phase = Phase.WORK
        self.remaining_seconds = self._duration_for_phase(self.phase)
        self.running = False

    def get_state(self) -> dict:
        return {
            "phase": self.phase.value,
            "remaining_seconds": self.remaining_seconds,
            "running": self.running,
            "sessions_completed": self.sessions_completed,
        }

    def _duration_for_phase(self, phase: Phase) -> int:
        if phase == Phase.WORK:
            return self.work_minutes * 60
        elif phase == Phase.SHORT_BREAK:
            return self.short_break * 60
        else:
            return self.long_break * 60
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_timer.py -v
```

Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add app/services/timer.py tests/test_timer.py
git commit -m "feat: pomodoro timer state machine"
```

---

## Task 5: Pomodoro Router + Frontend

**Files:**
- Create: `app/routers/pomodoro.py`
- Create: `app/templates/pomodoro.html`
- Create: `static/pomodoro.js`
- Create: `tests/test_pomodoro_router.py`

- [ ] **Step 1: Write failing tests for pomodoro router**

Create `tests/test_pomodoro_router.py`:

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_pomodoro_panel_returns_html(client):
    response = client.get("/pomodoro/panel")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_pomodoro_state_returns_json(client):
    response = client.get("/pomodoro/state")
    assert response.status_code == 200
    data = response.json()
    assert "phase" in data
    assert "remaining_seconds" in data
    assert "running" in data


def test_pomodoro_start(client):
    response = client.post("/pomodoro/start")
    assert response.status_code == 200
    state = client.get("/pomodoro/state").json()
    assert state["running"] is True


def test_pomodoro_pause(client):
    client.post("/pomodoro/start")
    response = client.post("/pomodoro/pause")
    assert response.status_code == 200
    state = client.get("/pomodoro/state").json()
    assert state["running"] is False


def test_pomodoro_reset(client):
    client.post("/pomodoro/start")
    response = client.post("/pomodoro/reset")
    assert response.status_code == 200
    state = client.get("/pomodoro/state").json()
    assert state["running"] is False
    assert state["remaining_seconds"] == 25 * 60


def test_pomodoro_skip(client):
    response = client.post("/pomodoro/skip")
    assert response.status_code == 200
    state = client.get("/pomodoro/state").json()
    assert state["phase"] == "short_break"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_pomodoro_router.py -v
```

Expected: FAIL — 404 for `/pomodoro/panel`

- [ ] **Step 3: Create pomodoro template**

Create `app/templates/pomodoro.html`:

```html
<h2>Pomodoro</h2>

<div class="timer-display" id="timer-container"
     data-remaining="{{ state.remaining_seconds }}"
     data-running="{{ state.running | lower }}"
     data-phase="{{ state.phase }}">
    <div class="phase-label">
        {% if state.phase == "work" %}Focus{% elif state.phase == "short_break" %}Short Break{% else %}Long Break{% endif %}
    </div>
    <div class="timer-countdown" id="countdown">
        {{ "%02d"|format(state.remaining_seconds // 60) }}:{{ "%02d"|format(state.remaining_seconds % 60) }}
    </div>
    <div class="session-count">Sessions: {{ state.sessions_completed }}</div>
</div>

<div class="timer-controls">
    {% if not state.running %}
    <button hx-post="/pomodoro/start" hx-target="#pomodoro-panel > div" hx-swap="innerHTML">Start</button>
    {% else %}
    <button hx-post="/pomodoro/pause" hx-target="#pomodoro-panel > div" hx-swap="innerHTML">Pause</button>
    {% endif %}
    <button hx-post="/pomodoro/reset" hx-target="#pomodoro-panel > div" hx-swap="innerHTML">Reset</button>
    <button hx-post="/pomodoro/skip" hx-target="#pomodoro-panel > div" hx-swap="innerHTML">Skip</button>
</div>
```

- [ ] **Step 4: Implement pomodoro router**

Create `app/routers/pomodoro.py`:

```python
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from app.services.timer import PomodoroTimer

router = APIRouter(prefix="/pomodoro")
templates = Jinja2Templates(directory="app/templates")

_timer: PomodoroTimer | None = None


def _get_timer(request: Request) -> PomodoroTimer:
    global _timer
    if _timer is None:
        config = request.app.state.config.pomodoro
        _timer = PomodoroTimer(
            work_minutes=config.work_minutes,
            short_break=config.short_break_minutes,
            long_break=config.long_break_minutes,
            long_break_interval=config.sessions_before_long_break,
        )
    return _timer


@router.get("/panel")
async def panel(request: Request):
    timer = _get_timer(request)
    return templates.TemplateResponse("pomodoro.html", {"request": request, "state": timer.get_state()})


@router.get("/state")
async def state(request: Request):
    timer = _get_timer(request)
    return JSONResponse(timer.get_state())


@router.post("/start")
async def start(request: Request):
    timer = _get_timer(request)
    timer.start()
    return templates.TemplateResponse("pomodoro.html", {"request": request, "state": timer.get_state()})


@router.post("/pause")
async def pause(request: Request):
    timer = _get_timer(request)
    timer.pause()
    return templates.TemplateResponse("pomodoro.html", {"request": request, "state": timer.get_state()})


@router.post("/reset")
async def reset(request: Request):
    timer = _get_timer(request)
    timer.reset()
    return templates.TemplateResponse("pomodoro.html", {"request": request, "state": timer.get_state()})


@router.post("/skip")
async def skip(request: Request):
    timer = _get_timer(request)
    timer.skip()
    return templates.TemplateResponse("pomodoro.html", {"request": request, "state": timer.get_state()})
```

- [ ] **Step 5: Register router in main.py**

Add to `app/main.py`:

```python
from app.routers import dashboard, tasks, pomodoro

app.include_router(pomodoro.router)
```

- [ ] **Step 6: Create client-side timer JS**

Create `static/pomodoro.js`:

```javascript
(function() {
    let interval = null;

    function startCountdown() {
        if (interval) clearInterval(interval);

        interval = setInterval(() => {
            const container = document.getElementById("timer-container");
            if (!container) { clearInterval(interval); return; }

            const running = container.dataset.running === "true";
            if (!running) { clearInterval(interval); return; }

            let remaining = parseInt(container.dataset.remaining, 10);
            if (remaining <= 0) {
                clearInterval(interval);
                htmx.ajax("POST", "/pomodoro/skip", {target: "#pomodoro-panel > div", swap: "innerHTML"});
                return;
            }

            remaining -= 1;
            container.dataset.remaining = remaining;
            const minutes = Math.floor(remaining / 60);
            const seconds = remaining % 60;
            const display = document.getElementById("countdown");
            if (display) {
                display.textContent = String(minutes).padStart(2, "0") + ":" + String(seconds).padStart(2, "0");
            }
        }, 1000);
    }

    // Re-initialize after HTMX swaps new content
    document.addEventListener("htmx:afterSwap", function(event) {
        if (event.detail.target.closest("#pomodoro-panel")) {
            startCountdown();
        }
    });

    // Initial start
    document.addEventListener("DOMContentLoaded", function() {
        startCountdown();
    });
})();
```

- [ ] **Step 7: Run tests to verify they pass**

```bash
uv run pytest tests/test_pomodoro_router.py -v
```

Expected: All PASS

- [ ] **Step 8: Commit**

```bash
git add app/routers/pomodoro.py app/templates/pomodoro.html static/pomodoro.js app/main.py tests/test_pomodoro_router.py
git commit -m "feat: pomodoro timer panel with client-side countdown"
```

---

## Task 6: RSS Feed Service

**Files:**
- Create: `app/services/feeds.py`
- Create: `tests/test_feeds.py`

- [ ] **Step 1: Write failing tests for feed service**

Create `tests/test_feeds.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from app.services.feeds import FeedService, FeedItem


def _mock_feed_response():
    mock_feed = MagicMock()
    mock_feed.bozo = False
    mock_feed.entries = [
        MagicMock(
            title="Test Article",
            link="https://example.com/article",
            published_parsed=(2026, 5, 19, 10, 0, 0, 0, 139, 0),
            get=lambda k, d=None: {"summary": "This is a test article summary that is long enough."}.get(k, d),
        ),
    ]
    mock_feed.feed = MagicMock(title="Test Blog")
    return mock_feed


def test_fetch_feeds_returns_items():
    service = FeedService()
    with patch("app.services.feeds.feedparser.parse", return_value=_mock_feed_response()):
        items = service.fetch_feed("https://example.com/feed.xml", "Test Blog")
    assert len(items) == 1
    assert items[0].title == "Test Article"
    assert items[0].link == "https://example.com/article"
    assert items[0].source == "Test Blog"


def test_fetch_feeds_caches_results():
    service = FeedService()
    mock_resp = _mock_feed_response()
    with patch("app.services.feeds.feedparser.parse", return_value=mock_resp) as mock_parse:
        service.fetch_feed("https://example.com/feed.xml", "Test Blog")
        service.fetch_feed("https://example.com/feed.xml", "Test Blog")
    assert mock_parse.call_count == 1


def test_fetch_feeds_respects_ttl():
    service = FeedService(cache_ttl_seconds=0)
    mock_resp = _mock_feed_response()
    with patch("app.services.feeds.feedparser.parse", return_value=mock_resp) as mock_parse:
        service.fetch_feed("https://example.com/feed.xml", "Test Blog")
        service.fetch_feed("https://example.com/feed.xml", "Test Blog")
    assert mock_parse.call_count == 2


def test_mark_read():
    service = FeedService()
    service.mark_read("item-123")
    assert service.is_read("item-123")
    assert not service.is_read("item-456")
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_feeds.py -v
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement feed service**

Create `app/services/feeds.py`:

```python
import time
import hashlib
from dataclasses import dataclass
import feedparser


@dataclass
class FeedItem:
    title: str
    link: str
    summary: str
    source: str
    published: str
    item_id: str


class FeedService:
    def __init__(self, cache_ttl_seconds: int = 300):
        self._cache: dict[str, tuple[float, list[FeedItem]]] = {}
        self._read_items: set[str] = set()
        self._cache_ttl = cache_ttl_seconds

    def fetch_feed(self, url: str, name: str) -> list[FeedItem]:
        now = time.time()
        if url in self._cache:
            cached_time, cached_items = self._cache[url]
            if now - cached_time < self._cache_ttl:
                return cached_items

        parsed = feedparser.parse(url)
        items = []
        for entry in parsed.entries:
            item_id = hashlib.md5((entry.get("link", "") + entry.get("title", "")).encode()).hexdigest()
            summary = entry.get("summary", "")
            if len(summary) > 150:
                summary = summary[:150] + "..."
            pub = ""
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                pub = time.strftime("%Y-%m-%d %H:%M", entry.published_parsed)
            items.append(FeedItem(
                title=entry.get("title", "Untitled"),
                link=entry.get("link", ""),
                summary=summary,
                source=name,
                published=pub,
                item_id=item_id,
            ))
        self._cache[url] = (now, items)
        return items

    def fetch_all(self, feeds: list[dict]) -> list[FeedItem]:
        all_items = []
        for feed in feeds:
            try:
                items = self.fetch_feed(feed["url"], feed["name"])
                all_items.extend(items)
            except Exception:
                continue
        all_items.sort(key=lambda x: x.published, reverse=True)
        return all_items

    def mark_read(self, item_id: str) -> None:
        self._read_items.add(item_id)

    def is_read(self, item_id: str) -> bool:
        return item_id in self._read_items
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_feeds.py -v
```

Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add app/services/feeds.py tests/test_feeds.py
git commit -m "feat: RSS feed service with caching and mark-as-read"
```

---

## Task 7: RSS Router

**Files:**
- Create: `app/routers/rss.py`
- Create: `app/templates/rss.html`
- Create: `tests/test_rss_router.py`

- [ ] **Step 1: Write failing tests for RSS router**

Create `tests/test_rss_router.py`:

```python
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.config import FeedEntry
from app.services.feeds import FeedItem


@pytest.fixture
def client():
    app.state.config.rss.feeds = [FeedEntry(url="https://example.com/feed.xml", name="Test")]
    return TestClient(app)


def test_rss_panel_returns_html(client):
    mock_items = [
        FeedItem(title="Article 1", link="https://example.com/1", summary="Summary 1", source="Test", published="2026-05-19 10:00", item_id="abc123"),
    ]
    with patch.object(app.state, "feed_service") as mock_svc:
        mock_svc.fetch_all.return_value = mock_items
        mock_svc.is_read.return_value = False
        response = client.get("/rss/panel")
    assert response.status_code == 200
    assert "Article 1" in response.text


def test_mark_read(client):
    with patch.object(app.state, "feed_service") as mock_svc:
        response = client.post("/rss/mark-read/abc123")
    assert response.status_code == 200
    mock_svc.mark_read.assert_called_once_with("abc123")
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_rss_router.py -v
```

Expected: FAIL

- [ ] **Step 3: Create RSS template**

Create `app/templates/rss.html`:

```html
<h2>RSS Feeds</h2>

{% if items %}
<ul class="feed-list">
    {% for item in items %}
    <li class="feed-item {% if item.is_read %}read{% endif %}">
        <a href="{{ item.link }}" target="_blank" class="feed-title">{{ item.title }}</a>
        <div class="feed-meta">
            <span class="feed-source">{{ item.source }}</span>
            <span class="feed-date">{{ item.published }}</span>
        </div>
        <p class="feed-summary">{{ item.summary }}</p>
        {% if not item.is_read %}
        <button hx-post="/rss/mark-read/{{ item.item_id }}" hx-target="#rss-panel > div" hx-swap="innerHTML" class="mark-read-btn">Mark read</button>
        {% endif %}
    </li>
    {% endfor %}
</ul>
{% else %}
<p class="empty-state">No feeds configured. Add feeds in config.yaml.</p>
{% endif %}
```

- [ ] **Step 4: Implement RSS router**

Create `app/routers/rss.py`:

```python
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter(prefix="/rss")
templates = Jinja2Templates(directory="app/templates")


@router.get("/panel")
async def rss_panel(request: Request):
    feed_service = request.app.state.feed_service
    config = request.app.state.config
    feeds = [{"url": f.url, "name": f.name} for f in config.rss.feeds]
    items = feed_service.fetch_all(feeds)
    items_with_read = [
        {**item.__dict__, "is_read": feed_service.is_read(item.item_id)}
        for item in items
    ]
    return templates.TemplateResponse("rss.html", {"request": request, "items": items_with_read})


@router.post("/mark-read/{item_id}")
async def mark_read(request: Request, item_id: str):
    feed_service = request.app.state.feed_service
    feed_service.mark_read(item_id)
    return await rss_panel(request)
```

- [ ] **Step 5: Register router and feed service in main.py**

Add to `app/main.py`:

```python
from app.routers import dashboard, tasks, pomodoro, rss
from app.services.feeds import FeedService

# After config loading
app.state.feed_service = FeedService(
    cache_ttl_seconds=app.state.config.rss.refresh_interval_minutes * 60
)

app.include_router(rss.router)
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
uv run pytest tests/test_rss_router.py -v
```

Expected: All PASS

- [ ] **Step 7: Commit**

```bash
git add app/routers/rss.py app/templates/rss.html app/main.py tests/test_rss_router.py
git commit -m "feat: RSS panel with feed fetching, caching, and mark-as-read"
```

---

## Task 8: Slack MCP Service

**Files:**
- Create: `app/services/slack_mcp.py`
- Create: `app/routers/slack.py`
- Create: `app/templates/slack.html`

- [ ] **Step 1: Implement Slack MCP client wrapper**

The Slack MCP server exposes tools like `slack_read_channel`. We'll use `httpx` to call it as an MCP client. The MCP server is assumed to be running (same one used by Claude Code).

Create `app/services/slack_mcp.py`:

```python
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
        # MCP stdio protocol: send a JSON-RPC request to the server process
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
                    # Parse the text content — format depends on MCP server implementation
                    messages.append(SlackMessage(
                        channel=channel,
                        author=item.get("author", "unknown"),
                        text=item.get("text", ""),
                        timestamp=item.get("timestamp", ""),
                    ))
            return messages
        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
            return []
```

Note: This is a placeholder implementation. The actual MCP transport (stdio vs SSE) and message format will depend on the specific Slack MCP server you have configured. We'll refine this during integration testing.

- [ ] **Step 2: Create Slack template**

Create `app/templates/slack.html`:

```html
<h2>Slack</h2>

{% if error %}
<p class="error-state">{{ error }}</p>
<button hx-get="/slack/panel" hx-target="#slack-panel > div" hx-swap="innerHTML">Retry</button>
{% elif messages %}
<ul class="message-list">
    {% for msg in messages %}
    <li class="slack-message">
        <div class="msg-header">
            <span class="msg-channel">#{{ msg.channel }}</span>
            <span class="msg-author">{{ msg.author }}</span>
            <span class="msg-time">{{ msg.timestamp }}</span>
        </div>
        <div class="msg-text">{{ msg.text }}</div>
    </li>
    {% endfor %}
</ul>
{% else %}
<p class="empty-state">No messages. Check your channel configuration.</p>
{% endif %}
```

- [ ] **Step 3: Implement Slack router**

Create `app/routers/slack.py`:

```python
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
    return templates.TemplateResponse("slack.html", {
        "request": request,
        "messages": all_messages,
        "error": error,
    })
```

- [ ] **Step 4: Register Slack router in main.py**

Add to `app/main.py`:

```python
from app.routers import dashboard, tasks, pomodoro, rss, slack

app.include_router(slack.router)
```

- [ ] **Step 5: Commit**

```bash
git add app/services/slack_mcp.py app/routers/slack.py app/templates/slack.html app/main.py
git commit -m "feat: slack panel with MCP client integration"
```

---

## Task 9: Polish and Integration

**Files:**
- Modify: `static/style.css`
- Modify: `app/templates/base.html`
- Modify: `config.yaml`

- [ ] **Step 1: Add panel-specific styles to CSS**

Append to `static/style.css`:

```css
/* Task panel */
.add-task-form {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 0.75rem;
}
.add-task-form input {
    flex: 1;
    padding: 0.4rem;
    background: #1a1a2e;
    border: 1px solid #0f3460;
    border-radius: 4px;
    color: #e0e0e0;
}
.add-task-form button {
    padding: 0.4rem 0.8rem;
    background: #e94560;
    border: none;
    border-radius: 4px;
    color: white;
    cursor: pointer;
}
.task-list { list-style: none; }
.task-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.3rem 0;
    border-bottom: 1px solid #0f3460;
}
.task-item.completed .task-text { text-decoration: line-through; opacity: 0.5; }
.checkbox {
    background: none;
    border: 1px solid #e94560;
    color: #e94560;
    cursor: pointer;
    font-family: monospace;
    padding: 0.1rem 0.3rem;
    border-radius: 3px;
}
.task-source { margin-left: auto; font-size: 0.75rem; opacity: 0.5; }

/* Pomodoro */
.timer-display { text-align: center; padding: 2rem 0; }
.phase-label { font-size: 0.9rem; text-transform: uppercase; opacity: 0.7; }
.timer-countdown { font-size: 3rem; font-family: monospace; margin: 0.5rem 0; }
.session-count { font-size: 0.8rem; opacity: 0.6; }
.timer-controls { display: flex; justify-content: center; gap: 0.5rem; }
.timer-controls button {
    padding: 0.5rem 1rem;
    background: #0f3460;
    border: 1px solid #e94560;
    border-radius: 4px;
    color: #e0e0e0;
    cursor: pointer;
}
.timer-controls button:hover { background: #e94560; }

/* Slack */
.message-list { list-style: none; }
.slack-message { padding: 0.5rem 0; border-bottom: 1px solid #0f3460; }
.msg-header { display: flex; gap: 0.5rem; font-size: 0.8rem; opacity: 0.7; }
.msg-channel { color: #e94560; }
.msg-text { margin-top: 0.25rem; }

/* RSS */
.feed-list { list-style: none; }
.feed-item { padding: 0.5rem 0; border-bottom: 1px solid #0f3460; }
.feed-item.read { opacity: 0.5; }
.feed-title { color: #4fc3f7; text-decoration: none; }
.feed-title:hover { text-decoration: underline; }
.feed-meta { font-size: 0.75rem; opacity: 0.6; margin-top: 0.2rem; }
.feed-source { color: #e94560; }
.feed-summary { font-size: 0.85rem; margin-top: 0.3rem; opacity: 0.8; }
.mark-read-btn {
    font-size: 0.7rem;
    background: none;
    border: 1px solid #0f3460;
    color: #e0e0e0;
    border-radius: 3px;
    cursor: pointer;
    margin-top: 0.3rem;
    padding: 0.2rem 0.5rem;
}

/* Shared */
.empty-state { opacity: 0.5; font-style: italic; }
.error-state { color: #e94560; }
```

- [ ] **Step 2: Update config.yaml with your real paths**

Update `config.yaml` with your actual Obsidian vault path (user fills this in):

```yaml
slack:
  channels:
    - general

tasks:
  vault_path: /path/to/your/obsidian/vault
  inbox_file: daily

pomodoro:
  work_minutes: 25
  short_break_minutes: 5
  long_break_minutes: 15
  sessions_before_long_break: 4

rss:
  feeds: []
  refresh_interval_minutes: 5
```

- [ ] **Step 3: Run all tests**

```bash
uv run pytest -v
```

Expected: All tests pass

- [ ] **Step 4: Manual verification — start the server and test in browser**

```bash
uv run uvicorn app.main:app --reload --port 8000
```

Open `http://localhost:8000` and verify:
- Dashboard loads with 4 panels in a 2x2 grid
- Tasks panel shows tasks from your vault (or empty state if vault not configured)
- Pomodoro timer starts, pauses, resets, and counts down
- RSS panel shows empty state (add a feed to config to test)
- Slack panel attempts connection (may show error if MCP server isn't running)

- [ ] **Step 5: Commit**

```bash
git add static/style.css config.yaml
git commit -m "feat: polish styles and finalize dashboard layout"
```

---

## Verification Plan

After completing all tasks:

1. **Unit tests:** `uv run pytest -v` — all pass
2. **Manual smoke test:** Start server with `uv run uvicorn app.main:app --reload --port 8000`
   - Visit `http://localhost:8000`
   - Add a task, toggle it, verify vault file changes
   - Start/pause/skip pomodoro timer
   - Add an RSS feed URL to config, reload, verify headlines appear
   - Verify Slack panel either shows messages or a graceful error
3. **HTMX polling:** Leave dashboard open for 60s, verify Slack panel refreshes without full page reload
