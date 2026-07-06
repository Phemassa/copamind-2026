"""Testes de integração do Bolão de IAs (serviço + API)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from copamind.data.repositories import DuckDBRepository
from copamind.pool.service import (
    leaderboard,
    lock_match_predictions,
    run_backtest,
)


def test_backtest_locks_and_scores(seeded_repo: DuckDBRepository) -> None:
    summary = run_backtest(seeded_repo)
    assert summary.matches_evaluated > 0
    assert summary.predictions_locked > 0
    assert len(summary.standings) == 2  # poisson + elo
    names = {s.predictor_name for s in summary.standings}
    assert names == {"poisson", "elo"}
    # Palpites e resultados foram persistidos.
    assert seeded_repo.count("pool_predictions") == summary.predictions_locked
    assert seeded_repo.count("pool_results") > 0


def test_predictions_are_immutable(seeded_repo: DuckDBRepository) -> None:
    matches = seeded_repo.list_finished_matches()
    target = matches[-1]  # partida com histórico suficiente
    locked = lock_match_predictions(seeded_repo, target)
    assert locked
    # Travar de novo não recria (idempotente) e não levanta erro.
    again = lock_match_predictions(seeded_repo, target)
    assert again == []


def test_insert_duplicate_raises(seeded_repo: DuckDBRepository) -> None:
    from datetime import UTC, datetime

    from copamind.data.schemas import PoolPrediction

    pred = PoolPrediction(
        prediction_id="poisson:M-000",
        predictor_name="poisson",
        match_id="M-000",
        snapshot_id="s",
        home_team_id="T-BRA",
        away_team_id="T-FRA",
        prob_home=0.5,
        prob_draw=0.3,
        prob_away=0.2,
        predicted_home_goals=1,
        predicted_away_goals=0,
        locked_at=datetime.now(UTC),
    )
    seeded_repo.insert_pool_prediction(pred)
    with pytest.raises(ValueError, match="travado"):
        seeded_repo.insert_pool_prediction(pred)


def test_leaderboard_points_non_negative(seeded_repo: DuckDBRepository) -> None:
    run_backtest(seeded_repo)
    standings = leaderboard(seeded_repo)
    for standing in standings:
        assert standing.total_points >= 0
        assert 0.0 <= standing.mean_brier <= 2.0


def test_pool_api(data_client: TestClient) -> None:
    response = data_client.post("/pool/backtest")
    assert response.status_code == 200
    body = response.json()
    assert body["matches_evaluated"] > 0
    assert len(body["standings"]) == 2

    leaderboard_response = data_client.get("/pool/leaderboard")
    assert leaderboard_response.status_code == 200
    assert len(leaderboard_response.json()) == 2

