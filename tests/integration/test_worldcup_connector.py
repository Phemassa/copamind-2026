"""Testes do conector OpenFootball worldcup.json e sua ingestão."""

from __future__ import annotations

from copamind.data.connectors.openfootball import read_worldcup_file
from copamind.data.ingestion.service import ingest_worldcup
from copamind.data.repositories import DuckDBRepository
from copamind.data.schemas import MatchStage, MatchStatus

_FIXTURE = "tests/fixtures/worldcup_sample.json"


def test_parse_worldcup_teams_and_matches() -> None:
    teams, matches = read_worldcup_file(_FIXTURE, snapshot_id="wc-test")
    codes = {t.fifa_code for t in teams}
    assert codes == {"ALP", "BET", "GAM", "DEL"}
    assert len(matches) == 3
    assert all(m.source == "openfootball" for m in matches)
    assert all(m.neutral_venue for m in matches)


def test_worldcup_scores_and_status() -> None:
    _, matches = read_worldcup_file(_FIXTURE, snapshot_id="wc-test")
    by_id = {m.match_id: m for m in matches}
    # Placar direto (score1/score2)
    assert by_id["WC-1"].home_score == 2
    assert by_id["WC-1"].status is MatchStatus.finished
    # Placar via score.ft
    assert by_id["WC-2"].home_score == 0
    assert by_id["WC-2"].away_score == 0
    # Final sem placar -> agendada
    assert by_id["WC-3"].status is MatchStatus.scheduled
    assert by_id["WC-3"].stage is MatchStage.final


def test_ingest_worldcup_into_repo() -> None:
    with DuckDBRepository(":memory:") as repo:
        result = ingest_worldcup(repo, _FIXTURE, snapshot_id="wc-test")
        assert result.teams == 4
        assert result.matches == 3
        assert repo.count("teams") == 4
        assert repo.latest_snapshot_id() == "wc-test"
        # Times sem confederação (OpenFootball não fornece)
        team = repo.get_team("T-ALP")
        assert team is not None
        assert team.confederation is None
