"""Conector do OpenFootball `worldcup.json` (MASTER_PLAN §37.11, DECISIONS ADR-0012).

Lê o formato estático (offline, redistribuível) e mapeia para os schemas do
CopaMind. Tolerante a variações de formato entre edições do dataset.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from copamind.data.schemas import Match, MatchStage, MatchStatus, Team

_SOURCE = "openfootball"


def _team_name(raw: Any) -> str:
    if isinstance(raw, str):
        return raw.strip()
    if isinstance(raw, dict):
        return str(raw.get("name") or raw.get("key") or "").strip()
    return ""


def _team_code(raw: Any, name: str) -> str:
    if isinstance(raw, dict):
        code = raw.get("code") or raw.get("key")
        if code:
            return str(code).upper()[:3]
    # Fallback determinístico a partir do nome (2-3 letras).
    letters = "".join(ch for ch in name.upper() if ch.isalpha())
    return (letters[:3] or "UNK").ljust(2, "X")


def _scores(match: dict[str, Any]) -> tuple[int | None, int | None]:
    if match.get("score1") is not None and match.get("score2") is not None:
        return int(match["score1"]), int(match["score2"])
    score = match.get("score")
    if isinstance(score, dict):
        ft = score.get("ft")
        if isinstance(ft, list) and len(ft) == 2:
            return int(ft[0]), int(ft[1])
    return None, None


def _stage(match: dict[str, Any], round_name: str) -> MatchStage:
    text = f"{match.get('group', '')} {round_name}".lower()
    if "final" in text and "semi" not in text and "quarter" not in text:
        return MatchStage.final
    if "semi" in text:
        return MatchStage.semifinal
    if "quarter" in text:
        return MatchStage.quarterfinal
    if "round of 16" in text or "16" in text:
        return MatchStage.round_of_16
    if "group" in text:
        return MatchStage.group
    return MatchStage.group


def _parse_date(value: Any) -> datetime:
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M"):
            try:
                return datetime.strptime(value[: len(fmt) + 2], fmt).replace(tzinfo=UTC)
            except ValueError:
                continue
    return datetime(2026, 6, 1, tzinfo=UTC)


def parse_worldcup_json(
    data: dict[str, Any], *, snapshot_id: str, collected_at: datetime | None = None
) -> tuple[list[Team], list[Match]]:
    """Converte o conteúdo de um `worldcup.json` em seleções e partidas."""
    collected_at = collected_at or datetime.now(UTC)
    teams: dict[str, Team] = {}
    matches: list[Match] = []

    def _ensure_team(raw: Any) -> str:
        name = _team_name(raw)
        if not name:
            return ""
        code = _team_code(raw, name)
        team_id = f"T-{code}"
        if team_id not in teams:
            teams[team_id] = Team(
                team_id=team_id,
                name=name,
                fifa_code=code,
                country=name,
                confederation=None,
                source=_SOURCE,
                collected_at=collected_at,
                available_at=collected_at,
                snapshot_id=snapshot_id,
            )
        return team_id

    competition = str(data.get("name", "World Cup"))
    for round_index, rnd in enumerate(data.get("rounds", [])):
        round_name = str(rnd.get("name", ""))
        for match_index, match in enumerate(rnd.get("matches", [])):
            home_id = _ensure_team(match.get("team1"))
            away_id = _ensure_team(match.get("team2"))
            if not home_id or not away_id or home_id == away_id:
                continue
            home_score, away_score = _scores(match)
            match_date = _parse_date(match.get("date"))
            status = (
                MatchStatus.finished
                if home_score is not None and away_score is not None
                else MatchStatus.scheduled
            )
            num = match.get("num", f"{round_index}-{match_index}")
            matches.append(
                Match(
                    match_id=f"WC-{num}",
                    competition=competition,
                    stage=_stage(match, round_name),
                    match_date=match_date,
                    home_team_id=home_id,
                    away_team_id=away_id,
                    neutral_venue=True,
                    home_score=home_score,
                    away_score=away_score,
                    status=status,
                    source=_SOURCE,
                    collected_at=collected_at,
                    available_at=match_date,
                    snapshot_id=snapshot_id,
                )
            )
    return list(teams.values()), matches


def read_worldcup_file(path: str | Path, *, snapshot_id: str) -> tuple[list[Team], list[Match]]:
    """Lê um arquivo `worldcup.json` local e o converte para os schemas."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("worldcup.json deve conter um objeto")
    return parse_worldcup_json(raw, snapshot_id=snapshot_id)
