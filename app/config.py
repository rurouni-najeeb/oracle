from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse
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
    repositories: list["GitHubRepository"] = field(default_factory=list)


@dataclass
class GitHubRepository:
    owner: str = ""
    repo: str = ""
    url: str = ""
    display_name: str = ""

    @property
    def label(self) -> str:
        return self.display_name or self.repo or self.url

    @property
    def full_name(self) -> str:
        if self.owner and self.repo:
            return f"{self.owner}/{self.repo}"
        return self.repo or self.url


def build_github_repository(value: str, display_name: str = "") -> GitHubRepository:
    owner, repo = _parse_github_repository(value)
    return GitHubRepository(
        owner=owner,
        repo=repo,
        url=f"https://github.com/{owner}/{repo}",
        display_name=display_name.strip(),
    )


def _parse_github_repository(value: str) -> tuple[str, str]:
    raw_value = value.strip()
    if not raw_value:
        raise ValueError("Repository is required.")

    if raw_value.startswith("git@github.com:"):
        repo_path = raw_value.removeprefix("git@github.com:")
    elif "://" in raw_value:
        parsed = urlparse(raw_value)
        if parsed.netloc.lower() not in {"github.com", "www.github.com"}:
            raise ValueError("Use a GitHub repository URL.")
        repo_path = parsed.path.strip("/")
    else:
        repo_path = (
            raw_value.removeprefix("github.com/")
            .removeprefix("www.github.com/")
            .strip("/")
        )

    parts = [part for part in repo_path.split("/") if part]
    if len(parts) < 2:
        raise ValueError("Use owner/repo or a GitHub repository URL.")

    owner = parts[0]
    repo = parts[1].removesuffix(".git")
    if not owner or not repo:
        raise ValueError("Use owner/repo or a GitHub repository URL.")
    return owner, repo


def _load_github_repository(entry: object) -> GitHubRepository | None:
    if isinstance(entry, str):
        try:
            return build_github_repository(entry)
        except ValueError:
            return None

    if not isinstance(entry, dict):
        return None

    owner = str(entry.get("owner", "")).strip()
    name = str(entry.get("name", "")).strip()
    repo = str(entry.get("repo", "")).strip()
    url = str(entry.get("url", "")).strip()
    display_name = str(entry.get("display_name", "") or entry.get("label", "")).strip()

    if url and name and not display_name:
        display_name = name
    if owner and name and not repo:
        repo = name

    if owner and repo:
        return GitHubRepository(
            owner=owner,
            repo=repo.removesuffix(".git"),
            url=url or f"https://github.com/{owner}/{repo.removesuffix('.git')}",
            display_name=display_name,
        )

    if url:
        try:
            parsed = build_github_repository(url, display_name)
            return parsed
        except ValueError:
            return None

    return None


@dataclass
class AppConfig:
    tasks: TasksConfig = field(default_factory=TasksConfig)
    pomodoro: PomodoroConfig = field(default_factory=PomodoroConfig)
    rss: RSSConfig = field(default_factory=RSSConfig)
    github: GitHubConfig = field(default_factory=GitHubConfig)


def load_config(path: Path) -> AppConfig:
    if not path.exists():
        return AppConfig()
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
    repositories = [
        repo
        for repo in (
            _load_github_repository(entry)
            for entry in github_data.get("repositories", [])
        )
        if repo is not None
    ]
    github = GitHubConfig(
        orgs=github_data.get("orgs", []),
        repositories=repositories,
    )

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
            "repositories": [
                {
                    "owner": repo.owner,
                    "repo": repo.repo,
                    "display_name": repo.display_name,
                    "url": repo.url,
                }
                for repo in config.github.repositories
            ],
        },
    }
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False)
