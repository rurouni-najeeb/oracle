import asyncio
import json
import logging
import shutil
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PullRequest:
    repo: str
    title: str
    number: int
    url: str
    status: str
    updated: str
    is_review_requested: bool


@dataclass
class GitHubData:
    review_requests: list[PullRequest]
    my_prs: list[PullRequest]
    commented: list[PullRequest]


@dataclass
class _CacheEntry:
    result: GitHubData
    ts: float


_cache: _CacheEntry | None = None
_cache_ttl: int = 120

_GH_PATH: str = shutil.which("gh") or "/opt/homebrew/bin/gh"


async def _run_gh(args: list[str]) -> str:
    proc = await asyncio.create_subprocess_exec(
        _GH_PATH,
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        logger.warning(
            "gh command failed (exit %d): %s", proc.returncode, stderr.decode().strip()
        )
    return stdout.decode()


async def fetch_github_data(orgs: list[str]) -> GitHubData:
    global _cache
    if _cache and (time.time() - _cache.ts) < _cache_ttl:
        return _cache.result

    review_requests = await _fetch_review_requests(orgs)
    my_prs = await _fetch_my_prs(orgs)
    commented = await _fetch_commented_prs(orgs)

    result = GitHubData(
        review_requests=review_requests, my_prs=my_prs, commented=commented
    )
    _cache = _CacheEntry(result=result, ts=time.time())
    return result


async def _fetch_review_requests(orgs: list[str]) -> list[PullRequest]:
    query = "is:open is:pr review-requested:@me archived:false"
    for org in orgs:
        query += f" org:{org}"

    output = await _run_gh(
        [
            "search",
            "prs",
            query,
            "--json",
            "repository,title,number,url,updatedAt,reviewDecision",
            "--limit",
            "10",
        ]
    )
    if not output.strip():
        return []

    items = json.loads(output)
    return [
        PullRequest(
            repo=item["repository"]["name"],
            title=item["title"],
            number=item["number"],
            url=item["url"],
            status=item.get("reviewDecision", "") or "pending",
            updated=item["updatedAt"][:10],
            is_review_requested=True,
        )
        for item in items
    ]


async def _fetch_my_prs(orgs: list[str]) -> list[PullRequest]:
    query = "is:open is:pr author:@me archived:false"
    for org in orgs:
        query += f" org:{org}"

    output = await _run_gh(
        [
            "search",
            "prs",
            query,
            "--json",
            "repository,title,number,url,updatedAt,reviewDecision",
            "--limit",
            "10",
        ]
    )
    if not output.strip():
        return []

    items = json.loads(output)
    return [
        PullRequest(
            repo=item["repository"]["name"],
            title=item["title"],
            number=item["number"],
            url=item["url"],
            status=item.get("reviewDecision", "") or "pending",
            updated=item["updatedAt"][:10],
            is_review_requested=False,
        )
        for item in items
    ]


async def _fetch_commented_prs(orgs: list[str]) -> list[PullRequest]:
    org_query = "+".join(f"org:{org}" for org in orgs)
    query = f"is:open+is:pr+commenter:@me+-author:@me+{org_query}"

    output = await _run_gh(
        [
            "api",
            f"search/issues?q={query}&per_page=10&sort=updated&order=desc",
            "--jq",
            '.items[] | {title: .title, number: .number, url: .html_url, repo: (.repository_url | split("/") | .[-1]), updated: .updated_at}',
        ]
    )
    if not output.strip():
        return []

    prs = []
    for line in output.strip().split("\n"):
        item = json.loads(line)
        prs.append(
            PullRequest(
                repo=item["repo"],
                title=item["title"],
                number=item["number"],
                url=item["url"],
                status="commented",
                updated=item["updated"][:10],
                is_review_requested=False,
            )
        )
    return prs
