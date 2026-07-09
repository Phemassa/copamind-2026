"""Testes do conector FIFA de fixtures."""

from __future__ import annotations

import json
from pathlib import Path

from copamind.data.fifa_fixtures import FIFAFixtureConnector, parse_fifa_matches
from copamind.data.repositories import DuckDBRepository


def _fixture_payload() -> dict[str, object]:
    return {
        "Results": [
            {
                "IdMatch": "1001",
                "Date": "2026-06-11T20:00:00Z",
                "StageName": "Group",
                "Home": {"Name": "Brazil"},
                "Away": {"Name": "Norway"},
            },
            {
                "IdMatch": "1002",
                "Date": "2026-06-12T20:00:00Z",
                "StageName": "Round of 32",
                "Home": {"Name": "France", "Score": 2},
                "Away": {"Name": "Senegal", "Score": 1},
            },
        ]
    }


def test_parse_fifa_matches() -> None:
    matches = parse_fifa_matches(_fixture_payload())
    assert len(matches) == 2
    assert matches[0].home_team_id == "T-BRA"
    assert matches[0].away_team_id == "T-NOR"
    assert matches[1].status == "finished"
    assert matches[1].home_score == 2


def test_refresh_uses_cache_without_network(tmp_path: Path) -> None:
    connector = FIFAFixtureConnector(cache_dir=tmp_path)
    cache_path = connector._cache_path("fixtures")
    cache_path.write_text(json.dumps(_fixture_payload()), encoding="utf-8")
    with DuckDBRepository(":memory:") as repo:
        result = connector.refresh(repo, force_network=False)
        assert result.matches == 2
        assert repo.count("matches") == 2
