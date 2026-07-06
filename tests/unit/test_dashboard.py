"""Testes dos helpers de dashboard."""

from __future__ import annotations

import pytest

from copamind.data.repositories import DuckDBRepository
from copamind.ui.dashboard import (
    championship_table,
    database_status,
    match_prediction_view,
    team_analysis_view,
)


def test_database_status(seeded_repo: DuckDBRepository) -> None:
    status = database_status(seeded_repo)
    assert status["teams"] == 48
    assert status["matches"] == 92
    assert status["snapshot"] == "copa2026-07-06"


def test_championship_table(seeded_repo: DuckDBRepository) -> None:
    rows = championship_table(seeded_repo, iterations=500)
    assert len(rows) >= 2
    total_title = sum(r["title"] for r in rows)
    assert total_title == pytest.approx(1.0, abs=1e-9)


def test_team_analysis_view(seeded_repo: DuckDBRepository) -> None:
    view = team_analysis_view(seeded_repo, "T-BRA")
    assert view["team_id"] == "T-BRA"
    assert isinstance(view["elo_rating"], float)
    assert len(view["windows"]) == 3
    assert len(view["last_matches"]) == 5


def test_match_prediction_view(seeded_repo: DuckDBRepository) -> None:
    view = match_prediction_view(seeded_repo, "T-BRA", "T-FRA")
    total = view["prob_home_win"] + view["prob_draw"] + view["prob_away_win"]
    assert abs(total - 1.0) < 1e-6
    # não persiste
    assert seeded_repo.count("predictions") == 0


