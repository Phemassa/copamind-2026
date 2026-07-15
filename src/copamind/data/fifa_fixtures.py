"""Conector leve para fixtures/standings da FIFA com cache local."""

from __future__ import annotations

import hashlib
import json
import urllib.parse
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

from copamind.data.connectors.flags import lookup
from copamind.data.repositories import DuckDBRepository
from copamind.data.schemas import Match, MatchStage, MatchStatus, Snapshot

CMS_API = "https://cxm-api.fifa.com/fifaplusweb/api"
CALENDAR_API = "https://api.fifa.com/api/v3/calendar/matches"
STANDINGS_PAGE = "/pt/tournaments/mens/worldcup/canadamexicousa2026/standings"
COMPETITION_ID = "17"
SEASON_ID = "285023"
SNAPSHOT_ID = "fifa-worldcup-2026"
DEFAULT_CACHE_DIR = Path("data/cache/fifa")


@dataclass(frozen=True)
class FIFARefreshResult:
    """Resumo da atualizacao FIFA."""

    matches: int
    source: str
    cache_path: Path | None = None
    warning: str | None = None


class FIFAFixtureConnector:
    """Busca fixtures oficiais e mantem cache local de seguranca."""

    def __init__(
        self,
        *,
        cache_dir: Path = DEFAULT_CACHE_DIR,
        client: httpx.Client | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._client = client or httpx.Client(
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0"},
        )

    def refresh(self, repo: DuckDBRepository, *, force_network: bool = False) -> FIFARefreshResult:
        """Atualiza DuckDB usando rede quando pedido, com fallback para cache."""
        repo.create_schema()
        data: dict[str, Any] | None = None
        cache_path = self._cache_path("fixtures")
        warning: str | None = None
        source = "cache"

        if not force_network and cache_path.exists():
            data = json.loads(cache_path.read_text(encoding="utf-8"))
        else:
            try:
                data = self.fetch_fixtures()
                cache_path.write_text(
                    json.dumps(data, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                source = "network"
            except httpx.HTTPError as exc:
                warning = f"falha ao atualizar FIFA; usando cache local: {exc}"
                if cache_path.exists():
                    data = json.loads(cache_path.read_text(encoding="utf-8"))
                else:
                    return FIFARefreshResult(0, "unavailable", None, warning)

        matches = parse_fifa_matches(data)
        if not matches:
            return FIFARefreshResult(0, source, cache_path, warning or "nenhuma fixture mapeavel")
        now = datetime.now(UTC)
        repo.upsert_snapshot(
            Snapshot(
                snapshot_id=SNAPSHOT_ID,
                created_at=now,
                description="FIFA World Cup 2026 fixtures cache",
                dataset_version="fifa-2026",
            )
        )
        repo.upsert_matches(matches)
        return FIFARefreshResult(len(matches), source, cache_path, warning)

    def fetch_standings_metadata(self) -> dict[str, Any]:
        """Busca metadados da pagina oficial de classificacao."""
        url = f"{CMS_API}/pages{STANDINGS_PAGE}"
        return self._get_json(url)

    def fetch_fixtures(self) -> dict[str, Any]:
        """Busca fixtures no calendario FIFA v3."""
        self.fetch_standings_metadata()
        params = {
            "language": "pt",
            "count": "500",
            "idCompetition": COMPETITION_ID,
            "idSeason": SEASON_ID,
        }
        url = f"{CALENDAR_API}?{urllib.parse.urlencode(params)}"
        return self._get_json(url)

    def _get_json(self, url: str) -> dict[str, Any]:
        response = self._client.get(url)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError(f"resposta FIFA nao e objeto JSON: {url}")
        return data

    def _cache_path(self, name: str) -> Path:
        digest = hashlib.sha256(f"{COMPETITION_ID}:{SEASON_ID}:{name}".encode()).hexdigest()[:16]
        return self.cache_dir / f"{name}_{digest}.json"


def parse_fifa_matches(data: dict[str, Any]) -> list[Match]:
    """Extrai partidas de formatos FIFA ou de cache simplificado."""
    candidates = _candidate_matches(data)
    matches: list[Match] = []
    seen: set[str] = set()
    collected_at = datetime.now(UTC)
    for index, item in enumerate(candidates, 1):
        match = _match_from_item(item, index, collected_at)
        if match is None or match.match_id in seen:
            continue
        seen.add(match.match_id)
        matches.append(match)
    return sorted(matches, key=lambda item: (item.match_date, item.match_id))


def _candidate_matches(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, dict):
        for key in ("Results", "results", "matches", "fixtures", "items"):
            value = data.get(key)
            if isinstance(value, list):
                direct = [item for item in value if isinstance(item, dict)]
                if direct and any(_looks_like_match(item) for item in direct):
                    return direct
        nested: list[dict[str, Any]] = []
        for value in data.values():
            nested.extend(_candidate_matches(value))
        return nested
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict) and _looks_like_match(item)]
    return []


def _looks_like_match(item: dict[str, Any]) -> bool:
    keys = {key.casefold() for key in item}
    return bool(
        {"home", "away"} <= keys
        or {"hometeam", "awayteam"} <= keys
        or {"home_team", "away_team"} <= keys
        or {"hometeamid", "awayteamid"} <= keys
        or {"home_team_id", "away_team_id"} <= keys
        or {"homecompetitor", "awaycompetitor"} <= keys
        or {"home", "awaycompetitor"} <= keys
    )


def _match_from_item(
    item: dict[str, Any], index: int, collected_at: datetime
) -> Match | None:
    home_team_id = _team_id(_first(item, "home_team_id", "HomeTeamId"))
    away_team_id = _team_id(_first(item, "away_team_id", "AwayTeamId"))
    home_obj = _first(item, "home", "homeTeam", "Home", "HomeTeam", "homeCompetitor")
    away_obj = _first(item, "away", "awayTeam", "Away", "AwayTeam", "awayCompetitor")
    home_team_id = home_team_id or _team_id(home_obj)
    away_team_id = away_team_id or _team_id(away_obj)
    if home_team_id is None or away_team_id is None or home_team_id == away_team_id:
        return None

    match_id = str(
        _first(item, "match_id", "idMatch", "IdMatch", "id", "Id")
        or f"FIFA-2026-{index:03d}"
    )
    match_date = _parse_datetime(
        _first(item, "match_date", "Date", "date", "LocalDate", "utcDate")
    )
    stage = _parse_stage(_first(item, "stage", "StageName", "GroupName", "Matchday") or "group")
    home_score = _score(item, home_obj, "home")
    away_score = _score(item, away_obj, "away")
    status = (
        MatchStatus.finished
        if home_score is not None and away_score is not None
        else MatchStatus.scheduled
    )
    return Match(
        match_id=f"fifa:{match_id}",
        competition="FIFA World Cup 2026",
        stage=stage,
        match_date=match_date,
        home_team_id=home_team_id,
        away_team_id=away_team_id,
        neutral_venue=True,
        home_score=home_score,
        away_score=away_score,
        status=status,
        importance_weight=2.0 if stage is not MatchStage.group else 1.0,
        source="fifa",
        collected_at=collected_at,
        available_at=collected_at,
        snapshot_id=SNAPSHOT_ID,
    )


def _team_id(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, dict):
        for key in (
            "team_id",
            "TeamId",
            "idTeam",
            "IdTeam",
            "fifa_code",
            "code",
            "abbreviation",
            "Name",
            "name",
            "ShortClubName",
            "TeamName",
        ):
            found = _team_id(value.get(key))
            if found:
                return found
        return None
    text = str(value).strip()
    if text.startswith("T-"):
        return text
    return lookup(text)


def _score(item: dict[str, Any], side_obj: Any, side: str) -> int | None:
    keys = (f"{side}_score", f"{side}Score", f"{side.title()}Score")
    for key in keys:
        value = item.get(key)
        if value not in {None, ""}:
            return int(str(value))
    if isinstance(side_obj, dict):
        for key in ("score", "Score", "Goals", "goals"):
            value = side_obj.get(key)
            if value not in {None, ""}:
                return int(str(value))
    return None


def _parse_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    text = str(value or "").strip()
    if not text:
        return datetime(2026, 6, 11, tzinfo=UTC)
    text = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        parsed = datetime.strptime(text[:10], "%Y-%m-%d").replace(tzinfo=UTC)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _parse_stage(value: Any) -> MatchStage:
    text = _stage_text(value)
    if "segundas de final" in text or "round of 32" in text or "32" in text:
        return MatchStage.round_of_32
    if "oitava" in text or "round of 16" in text or "16" in text:
        return MatchStage.round_of_16
    if "quarta" in text or "quarter" in text:
        return MatchStage.quarterfinal
    if "semi" in text:
        return MatchStage.semifinal
    if "3º" in text or "3o" in text or "terceiro" in text or "third" in text or "bronze" in text or "3rd" in text:
        return MatchStage.third_place
    if text.strip() == "final" or text == "final":
        return MatchStage.final
    return MatchStage.group


def _stage_text(value: Any) -> str:
    if isinstance(value, list):
        descriptions = [
            str(item.get("Description") or item.get("description") or "")
            for item in value
            if isinstance(item, dict)
        ]
        return " ".join(descriptions).casefold()
    if isinstance(value, dict):
        return str(value.get("Description") or value.get("description") or value).casefold()
    return str(value).casefold()


def _first(item: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in item:
            return item[key]
    return None
