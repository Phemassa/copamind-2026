"""Extrai estatísticas oficiais de jogadores da página FIFA World Cup 2026."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any
from urllib.error import HTTPError

CMS_API = "https://cxm-api.fifa.com/fifaplusweb/api"
GAMEDAY_API = "https://gameday-prod.fifa.mangodev.co.uk/1-0"
PAGE_PATH = "/pt/tournaments/mens/worldcup/canadamexicousa2026/statistics/player-statistics"
OUTPUT_DIR = Path("data/fifa/player_statistics")
CACHE_DIR = Path("data/cache/fifa_gameday")

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}

BASE_COLUMNS = [
    "player_id",
    "team_external_id",
    "player_name_pt",
    "player_name_en",
    "team_name_pt",
    "team_name_en",
    "team_abbreviation",
    "position_code",
    "position_pt",
    "position_en",
    "player_image_url",
    "team_flag_url",
]


def refresh_player_statistics(output_dir: Path = OUTPUT_DIR) -> dict[str, Any]:
    """Atualiza os CSVs de estatisticas de jogadores e retorna um resumo."""
    output_dir.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    group = _get_player_stats_group()
    token = _get_gameday_token()
    manifest_rows: list[dict[str, Any]] = []
    glossary_rows: list[dict[str, Any]] = []

    for stats_group in group["stats"]:
        title = stats_group["title"]
        story_type = stats_group["mainStat"]
        rows, columns, stories_count, rankings_count = _fetch_group_rows(
            token, group["seasonId"], story_type
        )
        csv_path = output_dir / f"{_slug(title)}.csv"
        _write_csv(csv_path, rows, columns)
        manifest_rows.append(
            {
                "aba": title,
                "story_type": story_type,
                "season_id": group["seasonId"],
                "rankings": rankings_count,
                "paginas_ranking": stories_count,
                "linhas": len(rows),
                "colunas": len(columns),
                "arquivo": str(csv_path).replace("\\", "/"),
            }
        )
        glossary_rows.extend(_glossary_rows(title, story_type, stats_group.get("glossary", [])))
        print(f"{title}: {len(rows)} jogadores -> {csv_path}", flush=True)
        time.sleep(1.0)

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
    summary = refresh_player_statistics()
    print(
        f"Resumo jogadores: {summary['tabs']} abas, "
        f"{summary['rows']} linhas, {summary['files']} arquivos."
    )


def _get_player_stats_group() -> dict[str, Any]:
    page = _get_json(f"{CMS_API}/pages{PAGE_PATH}")
    section = next(
        item for item in page["sections"] if item["entryType"] == "sectionTopPerformerGroup"
    )
    return _get_json(f"{CMS_API}{section['entryEndpoint']}")


def _get_gameday_token() -> str:
    return str(_get_json(f"{CMS_API}/external/gameDay/token")["token"])


def _fetch_group_rows(
    token: str, season_id: str, story_type: str
) -> tuple[list[dict[str, Any]], list[str], int, int]:
    stories = _fetch_group_stories(token, season_id, story_type)
    rows_by_player: dict[str, dict[str, Any]] = {}
    rankings: set[str] = set()
    columns = list(BASE_COLUMNS)

    for story in stories:
        ranked_stat = _ranked_stat(story)
        rankings.add(ranked_stat)
        rank_column = f"rank_{_stat_column_name(ranked_stat)}"
        _append_unique(columns, rank_column)

        column_order = _tag_value(story["tags"], f"urn:gd:tag:story:{story_type}:column_order")
        if not isinstance(column_order, list):
            raise ValueError(f"column_order ausente para {story_type}")
        for stat_tag in column_order:
            _append_unique(columns, _stat_column_name(stat_tag))

        for actor in story["actors"]:
            key = actor.get("key", {})
            player_id = key.get("_externalSportsPersonId")
            team_external_id = key.get("_externalTeamId")
            if not player_id:
                continue
            row_key = f"{player_id}:{team_external_id or ''}"
            tags = {item["name"]: item.get("value") for item in actor["tags"]}
            metadata = _player_metadata(actor, tags, player_id, team_external_id)
            row = rows_by_player.setdefault(row_key, metadata)
            _fill_missing(row, metadata)
            row[rank_column] = actor.get("number")
            should_replace_stats = _should_replace_player_stats(row, tags)
            for stat_tag in column_order:
                column = _stat_column_name(stat_tag)
                value = tags.get(stat_tag)
                if should_replace_stats or not row.get(column):
                    row[column] = value

    rows = sorted(
        rows_by_player.values(),
        key=lambda item: (
            str(item.get("team_abbreviation") or ""),
            str(item.get("player_name_pt") or item.get("player_name_en") or ""),
        ),
    )
    return rows, columns, len(stories), len(rankings)


def _fetch_group_stories(token: str, season_id: str, story_type: str) -> list[dict[str, Any]]:
    ranked_stats = _fetch_ranked_stats(token, season_id, story_type)
    stories: list[dict[str, Any]] = []
    for ranked_stat in ranked_stats:
        stories.extend(_fetch_ranked_stories(token, season_id, story_type, ranked_stat))
        time.sleep(0.8)
    if not stories:
        raise ValueError(f"nenhum ranking encontrado para {story_type}")
    return stories


def _fetch_ranked_stats(token: str, season_id: str, story_type: str) -> list[str]:
    query = (
        "(and resourceStatus==`urn:gd:resourceStatus:active` "
        f"_externalId~`urn:gd:story:classification:{story_type}:competitionId:{season_id}:"
        "(.*):rank_asc:page:1$`)"
    )
    params = {
        "query": query,
        "skip": "0",
        "limit": "20",
        "sort": "tags.name==urn:gd:tag:story:fifa:column_number:asc",
    }
    url = f"{GAMEDAY_API}/stories?{urllib.parse.urlencode(params)}"
    data = _get_json(url, token=token, cache=True)
    ranked_stats = [_ranked_stat(story) for story in data.get("items", [])]
    if not ranked_stats:
        raise ValueError(f"nenhum ranking encontrado para {story_type}")
    return ranked_stats


def _fetch_ranked_stories(
    token: str, season_id: str, story_type: str, ranked_stat: str
) -> list[dict[str, Any]]:
    query = (
        "(and resourceStatus==`urn:gd:resourceStatus:active` "
        f"_externalId~`urn:gd:story:classification:{story_type}:competitionId:{season_id}:"
        f"{ranked_stat}:rank_asc:page:(.*)$`)"
    )
    stories: list[dict[str, Any]] = []
    skip = 0
    limit = 20
    while True:
        params = {
            "query": query,
            "skip": str(skip),
            "limit": str(limit),
            "sort": "tags.name==urn:gd:tag:story:fifa:column_number:asc",
        }
        url = f"{GAMEDAY_API}/stories?{urllib.parse.urlencode(params)}"
        data = _get_json(url, token=token, cache=True)
        items = data.get("items", [])
        stories.extend(items)
        match_count = int(data.get("matchCount") or len(stories))
        skip += len(items)
        if skip >= match_count or not items:
            break
        time.sleep(0.5)
    return stories


def _player_metadata(
    actor: dict[str, Any],
    tags: dict[str, Any],
    player_id: str,
    team_external_id: str | None,
) -> dict[str, Any]:
    name = actor.get("name", {})
    return {
        "player_id": player_id,
        "team_external_id": team_external_id,
        "player_name_pt": name.get("por") or tags.get("urn:gd:tag:story:staff:display_name:por"),
        "player_name_en": name.get("eng") or tags.get("urn:gd:tag:story:staff:display_name:eng"),
        "team_name_pt": tags.get("urn:gd:tag:story:team:name:por"),
        "team_name_en": tags.get("urn:gd:tag:story:team:name:eng"),
        "team_abbreviation": tags.get("urn:gd:tag:story:team:abbreviation"),
        "position_code": tags.get("urn:gd:tag:story:staff:position"),
        "position_pt": tags.get("urn:gd:tag:story:staff:position:description:por"),
        "position_en": tags.get("urn:gd:tag:story:staff:position:description:eng"),
        "player_image_url": tags.get("urn:gd:tag:story:staff:image"),
        "team_flag_url": tags.get("urn:gd:tag:story:team:image"),
    }


def _write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str] | None = None) -> None:
    if not rows:
        path.write_text("", encoding="utf-8-sig")
        return
    columns = columns or list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)


def _get_json(url: str, *, token: str | None = None, cache: bool = False) -> dict[str, Any]:
    cache_path = _cache_path(url) if cache else None
    if cache_path and cache_path.exists() and os.getenv("COPAMIND_FIFA_READ_CACHE") == "1":
        return json.loads(cache_path.read_text(encoding="utf-8"))

    headers = dict(HEADERS)
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    for attempt in range(10):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                data = json.loads(response.read().decode("utf-8"))
                if cache_path:
                    cache_path.write_text(
                        json.dumps(data, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )
                return data
        except HTTPError as exc:
            if exc.code not in {429, 500, 502, 503, 504} or attempt == 9:
                raise
            retry_after = exc.headers.get("Retry-After")
            delay = (
                float(retry_after)
                if retry_after and retry_after.isdigit()
                else max(10.0, min(60.0, 2.0**attempt))
            )
            time.sleep(delay)
    raise RuntimeError(f"falha ao baixar JSON: {url}")


def _cache_path(url: str) -> Path:
    return CACHE_DIR / f"{hashlib.sha256(url.encode('utf-8')).hexdigest()}.json"


def _tag_value(tags: list[dict[str, Any]], name: str) -> Any:
    return next((tag.get("value") for tag in tags if tag.get("name") == name), None)


def _stat_column_name(tag: str) -> str:
    name = tag.rsplit(":", 1)[-1]
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def _ranked_stat(story: dict[str, Any]) -> str:
    external_id = story.get("_externalId") or story.get("key", {}).get("_externalId", "")
    match = re.search(r":competitionId:[^:]+:([^:]+):rank_asc:page:[^:]+$", external_id)
    if not match:
        raise ValueError(f"ranking sem stat identificável: {external_id}")
    return match.group(1)


def _append_unique(items: list[str], value: str) -> None:
    if value not in items:
        items.append(value)


def _fill_missing(row: dict[str, Any], values: dict[str, Any]) -> None:
    for key, value in values.items():
        if value and not row.get(key):
            row[key] = value


def _should_replace_player_stats(row: dict[str, Any], tags: dict[str, Any]) -> bool:
    """Evita que paginas antigas sobrescrevam acumulados mais recentes do mesmo atleta."""
    new_minutes = _num(tags.get("urn:gd:tag:football:stats:total_competition_minutes_played"))
    current_minutes = _num(row.get("total_competition_minutes_played"))
    if new_minutes and current_minutes:
        return new_minutes >= current_minutes
    if new_minutes and not current_minutes:
        return True
    new_goals = _num(tags.get("urn:gd:tag:football:stats:goals"))
    current_goals = _num(row.get("goals"))
    return bool(new_goals and new_goals >= current_goals)


def _num(value: object) -> float:
    if value in {None, ""}:
        return 0.0
    text = str(value).replace("%", "").replace("x", "").replace(",", ".").strip()
    try:
        return float(text)
    except ValueError:
        return 0.0


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
    normalized = unicodedata.normalize("NFKD", value.strip().lower())
    clean = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", "_", clean).strip("_")


if __name__ == "__main__":
    main()
