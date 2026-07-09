"""Extrai estatísticas oficiais de equipes da página FIFA World Cup 2026."""

from __future__ import annotations

import csv
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any
from urllib.error import HTTPError

CMS_API = "https://cxm-api.fifa.com/fifaplusweb/api"
GAMEDAY_API = "https://gameday-prod.fifa.mangodev.co.uk/1-0"
PAGE_PATH = "/pt/tournaments/mens/worldcup/canadamexicousa2026/statistics/team-statistics"
OUTPUT_DIR = Path("data/fifa/team_statistics")

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}


def refresh_team_statistics(output_dir: Path = OUTPUT_DIR) -> dict[str, Any]:
    """Atualiza os CSVs de estatisticas de equipes e retorna um resumo."""
    output_dir.mkdir(parents=True, exist_ok=True)
    group = _get_team_stats_group()
    token = _get_gameday_token()
    manifest_rows: list[dict[str, Any]] = []
    glossary_rows: list[dict[str, Any]] = []

    for stats_group in group["stats"]:
        title = stats_group["title"]
        story_type = stats_group["mainStat"]
        rows, columns, stories_count = _fetch_group_rows(token, group["seasonId"], story_type)
        csv_path = output_dir / f"{_slug(title)}.csv"
        _write_csv(csv_path, rows, columns)
        manifest_rows.append(
            {
                "aba": title,
                "story_type": story_type,
                "season_id": group["seasonId"],
                "rankings": stories_count,
                "linhas": len(rows),
                "colunas": len(columns),
                "arquivo": str(csv_path).replace("\\", "/"),
            }
        )
        glossary_rows.extend(_glossary_rows(title, story_type, stats_group.get("glossary", [])))
        print(f"{title}: {len(rows)} linhas -> {csv_path}")
        time.sleep(0.8)

    _write_csv(output_dir / "manifest.csv", manifest_rows)
    _write_csv(output_dir / "glossario.csv", glossary_rows)
    return {
        "tabs": len(manifest_rows),
        "rows": sum(int(row["linhas"]) for row in manifest_rows),
        "files": len(manifest_rows) + 2,
        "output_dir": str(output_dir).replace("\\", "/"),
        "manifest": manifest_rows,
    }


def main() -> None:
    summary = refresh_team_statistics()
    print(
        f"Resumo equipes: {summary['tabs']} abas, "
        f"{summary['rows']} linhas, {summary['files']} arquivos."
    )


def _get_team_stats_group() -> dict[str, Any]:
    page = _get_json(f"{CMS_API}/pages{PAGE_PATH}")
    section = next(
        item for item in page["sections"] if item["entryType"] == "sectionTopPerformerGroup"
    )
    return _get_json(f"{CMS_API}{section['entryEndpoint']}")


def _get_gameday_token() -> str:
    return str(_get_json(f"{CMS_API}/external/gameDay/token")["token"])


def _fetch_group_rows(
    token: str, season_id: str, story_type: str
) -> tuple[list[dict[str, Any]], list[str], int]:
    stories = _fetch_group_stories(token, season_id, story_type)
    rows_by_team: dict[str, dict[str, Any]] = {}
    columns = ["team_external_id", "team_name_pt", "team_name_en"]

    for story in stories:
        ranked_stat = _ranked_stat(story)
        rank_column = f"rank_{_stat_column_name(ranked_stat)}"
        _append_unique(columns, rank_column)

        column_order = _tag_value(story["tags"], f"urn:gd:tag:story:{story_type}:column_order")
        if not isinstance(column_order, list):
            raise ValueError(f"column_order ausente para {story_type}")
        for stat_tag in column_order:
            _append_unique(columns, _stat_column_name(stat_tag))

        for actor in story["actors"]:
            team_external_id = actor.get("key", {}).get("_externalId")
            if not team_external_id:
                continue
            row = rows_by_team.setdefault(
                team_external_id,
                {
                    "team_external_id": team_external_id,
                    "team_name_pt": actor.get("name", {}).get("por"),
                    "team_name_en": actor.get("name", {}).get("eng"),
                },
            )
            row[rank_column] = actor.get("number")
            tags = {item["name"]: item.get("value") for item in actor["tags"]}
            for stat_tag in column_order:
                row[_stat_column_name(stat_tag)] = tags.get(stat_tag)

    rows = sorted(rows_by_team.values(), key=lambda item: str(item.get("team_name_pt") or ""))
    return rows, columns, len(stories)


def _fetch_group_stories(token: str, season_id: str, story_type: str) -> list[dict[str, Any]]:
    query = (
        "(and resourceStatus==`urn:gd:resourceStatus:active` "
        f"_externalId~`urn:gd:story:classification:{story_type}:competitionId:{season_id}:"
        "(.*):rank_asc:page:1$`)"
    )
    stories: list[dict[str, Any]] = []
    skip = 0
    limit = 25
    while True:
        params = {
            "query": query,
            "skip": str(skip),
            "limit": str(limit),
            "sort": "tags.name==urn:gd:tag:story:fifa:column_number:asc",
        }
        url = f"{GAMEDAY_API}/stories?{urllib.parse.urlencode(params)}"
        data = _get_json(url, token=token)
        items = data.get("items", [])
        stories.extend(items)
        match_count = int(data.get("matchCount") or len(stories))
        skip += len(items)
        if skip >= match_count or not items:
            break
        time.sleep(0.8)
    if not stories:
        raise ValueError(f"nenhum ranking encontrado para {story_type}")
    return stories


def _write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str] | None = None) -> None:
    if not rows:
        path.write_text("", encoding="utf-8-sig")
        return
    columns = columns or list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)


def _get_json(url: str, *, token: str | None = None) -> dict[str, Any]:
    headers = dict(HEADERS)
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    for attempt in range(6):
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            if exc.code not in {429, 500, 502, 503, 504} or attempt == 5:
                raise
            retry_after = exc.headers.get("Retry-After")
            delay = float(retry_after) if retry_after and retry_after.isdigit() else 2**attempt
            time.sleep(delay)
    raise RuntimeError(f"falha ao baixar JSON: {url}")


def _tag_value(tags: list[dict[str, Any]], name: str) -> Any:
    return next((tag.get("value") for tag in tags if tag.get("name") == name), None)


def _stat_column_name(tag: str) -> str:
    name = tag.rsplit(":", 1)[-1]
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def _ranked_stat(story: dict[str, Any]) -> str:
    external_id = story.get("_externalId") or story.get("key", {}).get("_externalId", "")
    match = re.search(r":competitionId:[^:]+:([^:]+):rank_asc:page:1$", external_id)
    if not match:
        raise ValueError(f"ranking sem stat identificável: {external_id}")
    return match.group(1)


def _append_unique(items: list[str], value: str) -> None:
    if value not in items:
        items.append(value)


def _glossary_rows(
    tab_title: str, story_type: str, glossary: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    return [
        {
            "aba": tab_title,
            "story_type": story_type,
            "metric": item.get("identifier"),
            "description": item.get("value"),
        }
        for item in glossary
    ]


def _slug(value: str) -> str:
    replacements = {
        "ç": "c",
        "ã": "a",
        "á": "a",
        "â": "a",
        "é": "e",
        "ê": "e",
        "í": "i",
        "ó": "o",
        "õ": "o",
        "ú": "u",
        "ü": "u",
    }
    clean = value.lower()
    for source, target in replacements.items():
        clean = clean.replace(source, target)
    return re.sub(r"[^a-z0-9]+", "_", clean).strip("_")


if __name__ == "__main__":
    main()
