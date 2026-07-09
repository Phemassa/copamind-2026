"""Extras de partidas FIFA mantidos no cache bruto de fixtures."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from copamind.data.fifa_fixtures import DEFAULT_CACHE_DIR


def match_extra(match_id: str) -> dict[str, Any]:
    """Retorna metadados nao normalizados no schema principal."""
    return _match_extras().get(match_id, {})


@lru_cache(maxsize=1)
def _match_extras() -> dict[str, dict[str, Any]]:
    latest = _latest_fixture_cache()
    if latest is None:
        return {}
    data = json.loads(latest.read_text(encoding="utf-8"))
    extras: dict[str, dict[str, Any]] = {}
    for item in _candidate_match_dicts(data):
        raw_id = item.get("IdMatch") or item.get("idMatch") or item.get("id")
        if raw_id in {None, ""}:
            continue
        match_id = f"fifa:{raw_id}"
        home_penalties = _int_or_none(item.get("HomeTeamPenaltyScore"))
        away_penalties = _int_or_none(item.get("AwayTeamPenaltyScore"))
        home = item.get("Home") if isinstance(item.get("Home"), dict) else {}
        away = item.get("Away") if isinstance(item.get("Away"), dict) else {}
        winner_side = _winner_side(str(item.get("Winner") or ""), home, away)
        extras[match_id] = {
            "home_penalty_score": home_penalties,
            "away_penalty_score": away_penalties,
            "went_to_penalties": home_penalties is not None and away_penalties is not None,
            "went_to_extra_time": _went_to_extra_time(item),
            "winner_side": winner_side,
            "result_type": item.get("ResultType"),
            "match_time": item.get("MatchTime"),
        }
    return extras


def clear_match_extras_cache() -> None:
    """Limpa cache em memoria apos refresh FIFA."""
    _match_extras.cache_clear()


def _latest_fixture_cache() -> Path | None:
    files = sorted(DEFAULT_CACHE_DIR.glob("fixtures_*.json"), key=lambda path: path.stat().st_mtime)
    return files[-1] if files else None


def _candidate_match_dicts(data: Any) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    if isinstance(data, dict):
        if "IdMatch" in data or "idMatch" in data:
            found.append(data)
        for value in data.values():
            found.extend(_candidate_match_dicts(value))
    elif isinstance(data, list):
        for value in data:
            found.extend(_candidate_match_dicts(value))
    return found


def _winner_side(winner: str, home: dict[str, Any], away: dict[str, Any]) -> str | None:
    if not winner:
        return None
    if winner == str(home.get("IdTeam") or ""):
        return "home"
    if winner == str(away.get("IdTeam") or ""):
        return "away"
    return None


def _went_to_extra_time(item: dict[str, Any]) -> bool:
    if item.get("FirstHalfExtraTime") or item.get("SecondHalfExtraTime"):
        return True
    text = str(item.get("MatchTime") or "").replace("'", "").strip()
    try:
        return int(text) > 90
    except ValueError:
        return False


def _int_or_none(value: Any) -> int | None:
    if value in {None, ""}:
        return None
    try:
        return int(str(value))
    except ValueError:
        return None
