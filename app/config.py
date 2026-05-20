from dataclasses import dataclass, field
from pathlib import Path
import yaml


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
class GitHubConfig:
    orgs: list[str] = field(default_factory=list)


@dataclass
class AppConfig:
    tasks: TasksConfig = field(default_factory=TasksConfig)
    pomodoro: PomodoroConfig = field(default_factory=PomodoroConfig)
    rss: RSSConfig = field(default_factory=RSSConfig)
    github: GitHubConfig = field(default_factory=GitHubConfig)


def load_config(path: Path) -> AppConfig:
    with open(path) as f:
        data = yaml.safe_load(f) or {}

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
    feeds = [
        FeedEntry(url=f.get("url", ""), name=f.get("name", ""))
        for f in rss_data.get("feeds", [])
    ]
    rss = RSSConfig(
        feeds=feeds,
        refresh_interval_minutes=rss_data.get("refresh_interval_minutes", 5),
    )

    github_data = data.get("github", {})
    github = GitHubConfig(orgs=github_data.get("orgs", []))

    return AppConfig(tasks=tasks, pomodoro=pomodoro, rss=rss, github=github)


def save_config(config: AppConfig, path: Path) -> None:
    data = {
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
        "github": {
            "orgs": config.github.orgs,
        },
    }
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False)
