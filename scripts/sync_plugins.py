#!/usr/bin/env python3
"""Synchronize the README plugin table with dbx-store's official sources."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

SOURCE_URL = "https://raw.githubusercontent.com/t8y2/dbx-store/main/automation/plugin-sources.json"
API_URL = "https://api.github.com/repos/{}"
START = "<!-- dbx-plugin-table:start -->"
END = "<!-- dbx-plugin-table:end -->"


def get_json(url: str) -> dict:
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "awesome-dbx-plugins-sync"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        with urlopen(Request(url, headers=headers), timeout=30) as response:
            return json.load(response)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"failed to fetch {url}: {exc}") from exc


def validate_sources(payload: dict) -> list[str]:
    plugins = payload.get("plugins")
    if payload.get("version") != 1 or not isinstance(plugins, list) or not plugins:
        raise RuntimeError("official plugin-sources.json has an unexpected schema")
    repositories: list[str] = []
    for item in plugins:
        repository = item.get("repository") if isinstance(item, dict) else None
        if not isinstance(repository, str) or not re.fullmatch(r"[^/\s]+/[^/\s]+", repository):
            raise RuntimeError(f"invalid plugin repository: {repository!r}")
        if repository not in repositories:
            repositories.append(repository)
    return repositories


def render(repositories: list[str]) -> str:
    rows = ["| Repository | Star | Description |", "| --- | --- | --- |"]
    for repository in repositories:
        metadata = get_json(API_URL.format(repository))
        html_url = metadata.get("html_url") or f"https://github.com/{repository}"
        stars = metadata.get("stargazers_count")
        description = (metadata.get("description") or "").replace("|", "\\|").replace("\n", " ").strip()
        if not isinstance(stars, int) or not description:
            raise RuntimeError(f"repository metadata is incomplete for {repository}")
        rows.append(
            f"| [{repository}]({html_url}) | ![stars](https://img.shields.io/github/stars/{repository}?color=f2f08d&logo=github) | {description} |"
        )
    return "\n".join(rows)


def main() -> int:
    readme_path = Path(__file__).resolve().parents[1] / "README.md"
    readme = readme_path.read_text(encoding="utf-8")
    if START not in readme or END not in readme or readme.index(START) >= readme.index(END):
        raise RuntimeError("README.md is missing a valid plugin table marker pair")
    repositories = validate_sources(get_json(SOURCE_URL))
    table = render(repositories)
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    replacement = f"{START}\n{table}\n{END}"
    updated = pattern.sub(replacement, readme, count=1)
    if updated != readme:
        readme_path.write_text(updated, encoding="utf-8")
        print(f"Updated README.md with {len(repositories)} official plugins.")
    else:
        print("README.md is already up to date.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"sync failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
