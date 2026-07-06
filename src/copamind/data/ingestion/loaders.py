"""Leitores de CSV/JSON para seleções e partidas.

A validação de cada registro usa os schemas Pydantic (rejeição de dados
inválidos). A deduplicação remove repetições lógicas antes da persistência.
"""

from __future__ import annotations

import csv
import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from copamind.data.schemas import Match, Team


class IngestionError(Exception):
    """Erro de ingestão (arquivo inválido ou registros rejeitados)."""


def _read_records(path: str | Path) -> list[dict[str, Any]]:
    """Lê registros de um arquivo JSON (lista de objetos) ou CSV."""
    file_path = Path(path)
    if not file_path.exists():
        raise IngestionError(f"arquivo não encontrado: {file_path}")

    suffix = file_path.suffix.lower()
    if suffix == ".json":
        raw = json.loads(file_path.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            raise IngestionError("JSON deve conter uma lista de objetos")
        return [dict(item) for item in raw]
    if suffix == ".csv":
        with file_path.open(encoding="utf-8", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    raise IngestionError(f"formato não suportado: {suffix}")


def _validate(records: Iterable[dict[str, Any]], model: type[Team] | type[Match]) -> list[Any]:
    parsed: list[Any] = []
    for index, record in enumerate(records):
        try:
            parsed.append(model.model_validate(record))
        except ValidationError as exc:
            raise IngestionError(f"registro inválido na posição {index}: {exc}") from exc
    return parsed


def dedupe_teams(teams: list[Team]) -> list[Team]:
    """Remove seleções duplicadas por ``team_id`` (mantém a primeira)."""
    seen: set[str] = set()
    result: list[Team] = []
    for team in teams:
        if team.team_id in seen:
            continue
        seen.add(team.team_id)
        result.append(team)
    return result


def dedupe_matches(matches: list[Match]) -> list[Match]:
    """Remove partidas duplicadas.

    Considera duplicata tanto por ``match_id`` quanto pela chave lógica
    (home_team_id, away_team_id, match_date). Mantém a primeira ocorrência.
    """
    seen_ids: set[str] = set()
    seen_logical: set[tuple[str, str, str]] = set()
    result: list[Match] = []
    for match in matches:
        logical = (match.home_team_id, match.away_team_id, match.match_date.isoformat())
        if match.match_id in seen_ids or logical in seen_logical:
            continue
        seen_ids.add(match.match_id)
        seen_logical.add(logical)
        result.append(match)
    return result


def load_teams(path: str | Path) -> list[Team]:
    """Lê, valida e deduplica seleções de um arquivo JSON/CSV."""
    teams = _validate(_read_records(path), Team)
    return dedupe_teams(teams)


def load_matches(path: str | Path) -> list[Match]:
    """Lê, valida e deduplica partidas de um arquivo JSON/CSV."""
    matches = _validate(_read_records(path), Match)
    return dedupe_matches(matches)
