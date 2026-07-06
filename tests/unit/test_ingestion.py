"""Testes de ingestão (leitura, validação e deduplicação)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from copamind.data.ingestion import IngestionError, dedupe_matches, load_matches, load_teams
from copamind.data.schemas import Match, MatchStage, MatchStatus

_NOW = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
_LINEAGE = {
    "source": "test",
    "collected_at": _NOW,
    "available_at": _NOW,
    "snapshot_id": "snap-1",
}


def _match(match_id: str, home: str, away: str) -> Match:
    return Match(
        match_id=match_id,
        competition="c",
        stage=MatchStage.friendly,
        match_date=_NOW,
        home_team_id=home,
        away_team_id=away,
        home_score=1,
        away_score=0,
        status=MatchStatus.finished,
        **_LINEAGE,
    )


def test_load_sample_teams() -> None:
    teams = load_teams("data/samples/teams.json")
    assert len(teams) == 4
    assert {t.fifa_code for t in teams} == {"NTL", "SDR", "EST", "WST"}


def test_load_sample_matches() -> None:
    matches = load_matches("data/samples/matches.json")
    # 20 partidas únicas; as 2 duplicatas exatas do arquivo são removidas.
    assert len(matches) == 20
    assert all(m.status is MatchStatus.finished for m in matches)


def test_dedupe_matches_by_logical_key() -> None:
    a = _match("M-1", "T-1", "T-2")
    b = _match("M-2", "T-1", "T-2")  # mesmo confronto/data => duplicata lógica
    result = dedupe_matches([a, b])
    assert len(result) == 1


def test_missing_file() -> None:
    with pytest.raises(IngestionError):
        load_teams("data/samples/inexistente.json")


def test_invalid_record_rejected(tmp_path: Path) -> None:
    bad = tmp_path / "teams.json"
    bad.write_text(json.dumps([{"team_id": "T-1"}]), encoding="utf-8")
    with pytest.raises(IngestionError):
        load_teams(bad)


def test_unsupported_format(tmp_path: Path) -> None:
    bad = tmp_path / "teams.txt"
    bad.write_text("nope", encoding="utf-8")
    with pytest.raises(IngestionError):
        load_teams(bad)
