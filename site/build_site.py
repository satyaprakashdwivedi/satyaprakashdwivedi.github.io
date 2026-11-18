#!/usr/bin/env python3
"""Builds index.html: the public repositories with my commits in the last 30 days.

    GITHUB_TOKEN=... python3 site/build_site.py          # token optional locally, set automatically in Actions

Standard library only. Curated titles and highlights come from site/highlights.json; any other qualifying repo
still appears, using its GitHub description.
"""
import html
import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

USERNAME = "satyaprakashdwivedi"
ACTIVITY_WINDOW_DAYS = 30
SITE_FOLDER = Path(__file__).resolve().parent
OUTPUT_FILE = SITE_FOLDER.parent / "index.html"
SITE_URL = f"https://{USERNAME}.github.io"
EXCLUDED_REPOSITORIES = {f"{USERNAME}.github.io"}  # this site itself


def github_get(path):
    request = urllib.request.Request(f"https://api.github.com{path}",
                                     headers={"Accept": "application/vnd.github+json", "User-Agent": "profile-site-builder"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def my_recent_commits(repository_name, since, author_names):
    """Commits since `since` made by me: matched by GitHub login, or by name for commits from unlinked emails."""
    commits = github_get(f"/repos/{USERNAME}/{repository_name}/commits?since={since}&per_page=100")
    return [commit for commit in commits
            if (commit.get("author") or {}).get("login") == USERNAME
            or commit["commit"]["author"]["name"] in author_names]


def active_public_repositories(curated):
    since = (datetime.now(timezone.utc) - timedelta(days=ACTIVITY_WINDOW_DAYS)).strftime("%Y-%m-%dT%H:%M:%SZ")
    repositories = github_get(f"/users/{USERNAME}/repos?type=owner&per_page=100")
    active = []
    for repository in repositories:
        if (repository["private"] or repository["fork"] or repository["archived"]
                or repository["name"] in EXCLUDED_REPOSITORIES):
            continue
        commits = my_recent_commits(repository["name"], since, curated["author_names"])
        if not commits:
            continue
        details = curated["projects"].get(repository["name"], {})
        active.append({
            "name": repository["name"],
            "url": repository["html_url"],
            "title": details.get("title", repository["name"]),
            "summary": details.get("summary", repository.get("description") or ""),
            "highlights": details.get("highlights", []),
            "tags": details.get("tags", [repository["language"]] if repository.get("language") else []),
            "status": details.get("status"),
            "order": details.get("order", 100),
            "commit_count": len(commits),
            "last_commit": max(commit["commit"]["author"]["date"] for commit in commits),
        })
    active.sort(key=lambda project: (project["order"], project["last_commit"]))
    return active


def format_date(iso_timestamp):
    moment = datetime.strptime(iso_timestamp, "%Y-%m-%dT%H:%M:%SZ")
    return f"{moment.day} {moment:%b %Y}"


def render_project_card(project):
    escape = html.escape
    status_badge = f'<span class="status">{escape(project["status"])}</span>' if project["status"] else ""
    highlights = "".join(f"<li>{escape(item)}</li>" for item in project["highlights"])
    tags = "".join(f'<span class="tag">{escape(tag)}</span>' for tag in project["tags"])
    plural = "s" if project["commit_count"] != 1 else ""
    return f"""
      <article class="card">
        <header>
          <h3><a href="{escape(project['url'])}">{escape(project['title'])}</a></h3>{status_badge}
        </header>
        <p class="summary">{escape(project['summary'])}</p>
        {f'<ul class="highlights">{highlights}</ul>' if highlights else ''}
        <div class="tags">{tags}</div>
        <footer>
          <span>{project['commit_count']} commit{plural} in the last {ACTIVITY_WINDOW_DAYS} days · last {format_date(project['last_commit'])}</span>
          <a href="{escape(project['url'])}">View on GitHub →</a>
        </footer>
      </article>"""


def render_page(curated, projects):
    profile = curated["profile"]
    escape = html.escape
    focus_cards = "".join(f'<div class="focus"><h3>{escape(area["title"])}</h3><p>{escape(area["text"])}</p></div>'
                          for area in profile["focus"])
    built_rows = "".join(f'<li><strong>{escape(item["title"])}</strong> {escape(item["text"])}</li>'
                         for item in profile.get("built", []))
    project_cards = "".join(render_project_card(project) for project in projects) or \
        '<p class="empty">No public commits in the last 30 days.</p>'
    built_on = datetime.now(timezone.utc)
    template = (SITE_FOLDER / "template.html").read_text(encoding="utf-8")
    return (template
            .replace("{{NAME}}", escape(profile["name"]))
            .replace("{{HEADLINE}}", escape(profile["headline"]))
            .replace("{{SUMMARY}}", escape(profile["summary"]))
            .replace("{{GITHUB}}", escape(profile["github"]))
            .replace("{{LINKEDIN}}", escape(profile["linkedin"]))
            .replace("{{SITE_URL}}", SITE_URL)
            .replace("{{LOCATION}}", escape(profile.get("location", "")))
            .replace("{{BUILT}}", built_rows)
            .replace("{{FOCUS_CARDS}}", focus_cards)
            .replace("{{PROJECT_CARDS}}", project_cards)
            .replace("{{PROJECT_COUNT}}", str(len(projects)))
            .replace("{{WINDOW_DAYS}}", str(ACTIVITY_WINDOW_DAYS))
            .replace("{{BUILT_ON}}", f"{built_on.day} {built_on:%b %Y}"))


def main():
    curated = json.loads((SITE_FOLDER / "highlights.json").read_text(encoding="utf-8"))
    projects = active_public_repositories(curated)
    OUTPUT_FILE.write_text(render_page(curated, projects), encoding="utf-8")
    print(f"index.html: {len(projects)} active public projects: {', '.join(p['name'] for p in projects)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
