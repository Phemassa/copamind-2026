"""Testes das ferramentas do copamind-mcp."""

from __future__ import annotations

from copamind.data.repositories import DuckDBRepository
from copamind.mcp import tools
from copamind.pool.service import run_backtest


def test_list_and_get_team(seeded_repo: DuckDBRepository) -> None:
    teams = tools.list_teams(seeded_repo)
    assert len(teams) == 48
    team = tools.get_team(seeded_repo, "T-BRA")
    assert team is not None
    assert team["fifa_code"] == "BRA"
    assert tools.get_team(seeded_repo, "nope") is None


def test_last_matches_and_h2h(seeded_repo: DuckDBRepository) -> None:
    last = tools.get_last_matches(seeded_repo, "T-BRA", limit=3)
    assert len(last) == 3
    h2h = tools.get_head_to_head(seeded_repo, "T-BRA", "T-FRA")
    assert all({m["home_team_id"], m["away_team_id"]} == {"T-BRA", "T-FRA"} for m in h2h)


def test_predict_and_ensemble(seeded_repo: DuckDBRepository) -> None:
    pred = tools.predict_match(seeded_repo, "T-BRA", "T-FRA")
    total = pred["prob_home_win"] + pred["prob_draw"] + pred["prob_away_win"]
    assert abs(total - 1.0) < 1e-6
    ens = tools.ensemble_predict(seeded_repo, "T-BRA", "T-FRA")
    assert abs(ens["prob_home"] + ens["prob_draw"] + ens["prob_away"] - 1.0) < 1e-6


def test_simulation_tool(seeded_repo: DuckDBRepository) -> None:
    results = tools.run_tournament_simulation(seeded_repo, iterations=200)
    assert len(results) >= 2  # pelo menos 2 classificados
    total = sum(r["champion_probability"] for r in results)
    assert abs(total - 1.0) < 1e-9


def test_data_freshness(seeded_repo: DuckDBRepository) -> None:
    freshness = tools.get_data_freshness(seeded_repo)
    assert freshness["teams"] == 48
    assert freshness["matches"] == 92
    assert freshness["snapshot_id"] == "copa2026-07-06"


def test_pool_and_calibration_tools(seeded_repo: DuckDBRepository) -> None:
    run_backtest(seeded_repo)
    board = tools.get_pool_leaderboard(seeded_repo)
    assert len(board) == 2
    calib = tools.get_calibration(seeded_repo)
    assert calib


def test_search_knowledge_tool(seeded_repo: DuckDBRepository) -> None:
    tools.add_user_report(seeded_repo, "O Brasil venceu o México por 2 a 1.")
    results = tools.search_knowledge(seeded_repo, "Brasil México", top_k=3)
    assert results
    assert "Brasil" in results[0]["text"]


def test_write_tools_lifecycle(seeded_repo: DuckDBRepository) -> None:
    report = tools.add_user_report(seeded_repo, "O Brasil venceu o México por 2 a 1.")
    report_id = report["report_id"]
    assert report["verified"] is False
    verified = tools.verify_user_report(seeded_repo, report_id)
    assert verified is not None
    assert verified["verified"] is True
    assert tools.delete_user_report(seeded_repo, report_id) is True


def test_tool_groups_separated() -> None:
    read_names = {t.__name__ for t in tools.READ_ONLY_TOOLS}
    write_names = {t.__name__ for t in tools.WRITE_TOOLS}
    assert "list_teams" in read_names
    assert "add_user_report" in write_names
    assert read_names.isdisjoint(write_names)


