"""Collect public GitHub telemetry with the REST API.

The script intentionally uses only the Python standard library. The Actions-provided
GITHUB_TOKEN raises the API limit, but no personal token is required.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


API_ROOT = "https://api.github.com"


class GitHubApiError(RuntimeError):
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def iso_z(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def api_get(path: str, token: str | None) -> list | dict:
    request = urllib.request.Request(
        f"{API_ROOT}{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "afterinit-profile-telemetry",
            "X-GitHub-Api-Version": "2022-11-28",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")[:500]
        raise GitHubApiError(f"GitHub API returned HTTP {error.code}: {detail}") from error
    except urllib.error.URLError as error:
        raise GitHubApiError(f"GitHub API request failed: {error.reason}") from error


def fetch_public_data(username: str, token: str | None) -> tuple[list[dict], list[dict]]:
    encoded = urllib.parse.quote(username, safe="")
    events: list[dict] = []
    for page in range(1, 4):
        batch = api_get(f"/users/{encoded}/events/public?per_page=100&page={page}", token)
        if not isinstance(batch, list):
            raise GitHubApiError("Unexpected events response from GitHub")
        events.extend(batch)
        if len(batch) < 100:
            break

    repositories = api_get(
        f"/users/{encoded}/repos?type=owner&sort=pushed&direction=desc&per_page=100",
        token,
    )
    if not isinstance(repositories, list):
        raise GitHubApiError("Unexpected repositories response from GitHub")
    return events, repositories


def fetch_recent_commits(
    username: str,
    raw_events: list[dict],
    raw_repositories: list[dict],
    generated_at: datetime,
    token: str | None,
    excluded: set[str] | None = None,
) -> list[dict]:
    """Fetch exact commit metadata omitted from the public Events payload."""
    cutoff = generated_at - timedelta(days=8)
    active_names: list[str] = []
    excluded = excluded or set()
    for event in raw_events:
        if event.get("type") == "PushEvent":
            name = repo_name((event.get("repo") or {}).get("name"))
            if name.lower() not in excluded and name not in active_names:
                active_names.append(name)
    for repository in raw_repositories:
        pushed_at = parse_time(repository.get("pushed_at"))
        name = str(repository.get("name") or "")
        if name and name.lower() not in excluded and pushed_at and pushed_at >= cutoff and name not in active_names:
            active_names.append(name)

    encoded_user = urllib.parse.quote(username, safe="")
    since = urllib.parse.quote(iso_z(cutoff), safe="")
    collected: list[dict] = []
    for name in active_names[:8]:
        encoded_repo = urllib.parse.quote(name, safe="")
        encoded_author = urllib.parse.quote(username, safe="")
        try:
            batch = api_get(
                f"/repos/{encoded_user}/{encoded_repo}/commits?author={encoded_author}&since={since}&per_page=100",
                token,
            )
        except GitHubApiError as error:
            print(f"warning: could not read commits for {name}: {error}", file=sys.stderr)
            continue
        if not isinstance(batch, list):
            continue
        for item in batch:
            item["_telemetry_repo"] = name
        collected.extend(batch)
    return collected


def event_label(event_type: str, payload: dict) -> str:
    if event_type == "PushEvent":
        return "PUSH"
    if event_type == "CreateEvent":
        return "CREATE"
    if event_type == "PullRequestEvent":
        return f"PR {str(payload.get('action', '')).upper()}".strip()
    if event_type == "IssuesEvent":
        return f"ISSUE {str(payload.get('action', '')).upper()}".strip()
    return {
        "ForkEvent": "FORK",
        "ReleaseEvent": "RELEASE",
        "WatchEvent": "STAR",
        "DeleteEvent": "DELETE",
        "PublicEvent": "PUBLIC",
    }.get(event_type, event_type.removesuffix("Event").upper())


def repo_name(raw_name: str | None) -> str:
    if not raw_name:
        return "unknown"
    return raw_name.split("/", 1)[-1]


def normalize_events(raw_events: list[dict], excluded: set[str]) -> tuple[list[dict], list[dict]]:
    events: list[dict] = []
    commits: list[dict] = []
    seen_commits: set[tuple[str, str]] = set()

    for raw in raw_events:
        name = repo_name((raw.get("repo") or {}).get("name"))
        if name.lower() in excluded:
            continue
        payload = raw.get("payload") or {}
        event_type = str(raw.get("type") or "UnknownEvent")
        timestamp = raw.get("created_at")
        ref = str(payload.get("ref") or "")
        branch = ref.removeprefix("refs/heads/") if ref.startswith("refs/heads/") else ref
        raw_commits = payload.get("commits") if isinstance(payload.get("commits"), list) else []

        events.append(
            {
                "id": str(raw.get("id") or ""),
                "type": event_type,
                "action": event_label(event_type, payload),
                "timestamp": timestamp,
                "repo": name,
                "branch": branch or None,
                "commit_count": len(raw_commits) or int(payload.get("size") or 0),
            }
        )

        if event_type != "PushEvent":
            continue
        for item in raw_commits:
            sha = str(item.get("sha") or "")
            key = (name.lower(), sha)
            if not sha or key in seen_commits:
                continue
            seen_commits.add(key)
            commits.append(
                {
                    "sha": sha,
                    "message": str(item.get("message") or "untitled commit").splitlines()[0],
                    "repo": name,
                    "branch": branch or "—",
                    # Public events expose push time, not individual commit author time.
                    "timestamp": timestamp,
                }
            )

    events.sort(key=lambda item: item.get("timestamp") or "", reverse=True)
    commits.sort(key=lambda item: item.get("timestamp") or "", reverse=True)
    return events, commits


def normalize_commit_details(raw_commits: list[dict], excluded: set[str]) -> list[dict]:
    commits: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for item in raw_commits:
        name = str(item.get("_telemetry_repo") or "")
        sha = str(item.get("sha") or "")
        if not name or not sha or name.lower() in excluded:
            continue
        key = (name.lower(), sha)
        if key in seen:
            continue
        seen.add(key)
        commit = item.get("commit") or {}
        author = commit.get("author") or {}
        committer = commit.get("committer") or {}
        commits.append(
            {
                "sha": sha,
                "message": str(commit.get("message") or "untitled commit").splitlines()[0],
                "repo": name,
                "branch": "default",
                "timestamp": author.get("date") or committer.get("date"),
            }
        )
    commits.sort(key=lambda item: item.get("timestamp") or "", reverse=True)
    return commits


def normalize_repositories(raw_repos: list[dict], excluded: set[str]) -> list[dict]:
    repositories = []
    for raw in raw_repos:
        name = str(raw.get("name") or "")
        if not name or name.lower() in excluded or raw.get("fork") or raw.get("archived"):
            continue
        topics = raw.get("topics") if isinstance(raw.get("topics"), list) else []
        repositories.append(
            {
                "name": name,
                "description": raw.get("description"),
                "language": raw.get("language"),
                "topics": topics[:3],
                "pushed_at": raw.get("pushed_at"),
                "url": raw.get("html_url"),
            }
        )
    repositories.sort(key=lambda item: item.get("pushed_at") or "", reverse=True)
    return repositories


def latest_push(events: list[dict], commits: list[dict]) -> dict | None:
    push = next((event for event in events if event["type"] == "PushEvent"), None)
    if not push:
        return None
    push_time = parse_time(push.get("timestamp"))
    match = next((commit for commit in commits if commit["repo"] == push["repo"]), None)
    if match and push_time:
        commit_time = parse_time(match.get("timestamp"))
        if commit_time is None or abs((push_time - commit_time).total_seconds()) > 7 * 86400:
            match = None
    return {
        "timestamp": push["timestamp"],
        "repo": push["repo"],
        "branch": push.get("branch") or "—",
        "message": (match or {}).get("message") or "public push · commit detail unavailable",
        "commit_count": push["commit_count"] or (1 if match else 0),
    }


def build_stats(events: list[dict], commits: list[dict], generated_at: datetime, tz) -> dict:
    local_now = generated_at.astimezone(tz)
    today = local_now.date()
    dates = [today - timedelta(days=offset) for offset in range(6, -1, -1)]
    date_keys = {day.isoformat(): {"commits": 0, "pushes": 0} for day in dates}
    matrix = {day.isoformat(): [0] * 24 for day in dates}
    active_repos: Counter[str] = Counter()

    for event in events:
        moment = parse_time(event.get("timestamp"))
        if moment is None:
            continue
        local = moment.astimezone(tz)
        key = local.date().isoformat()
        if key not in date_keys:
            continue
        if event["type"] != "PushEvent":
            continue
        date_keys[key]["pushes"] += 1
        active_repos[event["repo"]] += 1

    for commit in commits:
        moment = parse_time(commit.get("timestamp"))
        if moment is None:
            continue
        local = moment.astimezone(tz)
        key = local.date().isoformat()
        if key not in date_keys:
            continue
        date_keys[key]["commits"] += 1
        matrix[key][local.hour] += 1
        active_repos[commit["repo"]] += 1

    daily = [
        {
            "date": day.isoformat(),
            "day": day.strftime("%a").upper(),
            **date_keys[day.isoformat()],
        }
        for day in dates
    ]
    return {
        "window_start": dates[0].isoformat(),
        "window_end": dates[-1].isoformat(),
        "commits": sum(item["commits"] for item in daily),
        "pushes": sum(item["pushes"] for item in daily),
        "active_repos": len(active_repos),
        "active_days": sum(1 for item in daily if item["pushes"] > 0),
        "most_active": active_repos.most_common(1)[0][0] if active_repos else None,
        "daily": daily,
        "matrix": [
            {"date": day.isoformat(), "day": day.strftime("%a").upper(), "hours": matrix[day.isoformat()]}
            for day in dates
        ],
    }


def build_document(
    username: str,
    raw_events: list[dict],
    raw_repos: list[dict],
    status: dict,
    generated_at: datetime,
    source: str,
    raw_commit_details: list[dict] | None = None,
) -> dict:
    exclusions = {str(name).lower() for name in status.get("exclude_repositories", [])}
    events, event_commits = normalize_events(raw_events, exclusions)
    detailed_commits = normalize_commit_details(raw_commit_details or [], exclusions)
    if detailed_commits:
        commits = detailed_commits
        branches = {event["repo"]: event.get("branch") or "default" for event in events if event["type"] == "PushEvent"}
        for commit in commits:
            commit["branch"] = branches.get(commit["repo"], "default")
    else:
        commits = event_commits
    repositories = normalize_repositories(raw_repos, exclusions)
    try:
        tz = ZoneInfo(status.get("timezone", "UTC"))
    except ZoneInfoNotFoundError:
        tz = timezone.utc
    return {
        "schema_version": 1,
        "username": username,
        "generated_at": iso_z(generated_at),
        "source": source,
        "events": events[:40],
        "commits": commits[:40],
        "repos": repositories[:12],
        "latest_push": latest_push(events, commits),
        "stats": build_stats(events, commits, generated_at, tz),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--username", default="afterinit")
    parser.add_argument("--status", type=Path, default=Path("data/status.json"))
    parser.add_argument("--output", type=Path, default=Path("data/activity.json"))
    parser.add_argument(
        "--fixture",
        type=Path,
        help="Read raw 'events' and 'repos' arrays from a local JSON fixture instead of the API.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        status = load_json(args.status)
        if args.fixture:
            fixture = load_json(args.fixture)
            raw_events = fixture.get("events", [])
            raw_repos = fixture.get("repos", [])
            raw_commits = fixture.get("commits", [])
            generated_at = parse_time(fixture.get("generated_at")) or utc_now()
            source = "fixture"
        else:
            raw_events, raw_repos = fetch_public_data(args.username, os.getenv("GITHUB_TOKEN"))
            generated_at = utc_now()
            raw_commits = fetch_recent_commits(
                args.username,
                raw_events,
                raw_repos,
                generated_at,
                os.getenv("GITHUB_TOKEN"),
                {str(name).lower() for name in status.get("exclude_repositories", [])},
            )
            source = "github-api"
        document = build_document(
            args.username,
            raw_events,
            raw_repos,
            status,
            generated_at,
            source,
            raw_commits,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(document, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    except (OSError, ValueError, GitHubApiError) as error:
        print(f"telemetry collection failed: {error}", file=sys.stderr)
        return 1

    print(
        f"collected {len(document['events'])} events, "
        f"{len(document['commits'])} commits, and {len(document['repos'])} repositories"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
