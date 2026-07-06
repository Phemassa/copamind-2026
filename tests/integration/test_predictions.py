"""Testes de integração da previsão (serviço + persistência + API)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from copamind.data.repositories import DuckDBRepository
from copamind.models.poisson.service import predict_match


def test_predict_and_persist(seeded_repo: DuckDBRepository) -> None:
    prediction = predict_match(seeded_repo, "T-BRA", "T-NOR")
    total = prediction.prob_home_win + prediction.prob_draw + prediction.prob_away_win
    assert abs(total - 1.0) < 1e-6
    assert seeded_repo.count("predictions") == 1


def test_predict_no_persist(seeded_repo: DuckDBRepository) -> None:
    predict_match(seeded_repo, "T-BRA", "T-NOR", persist=False)
    assert seeded_repo.count("predictions") == 0


def test_predict_api(data_client: TestClient) -> None:
    response = data_client.post(
        "/predictions/match",
        json={"home_team_id": "T-BRA", "away_team_id": "T-FRA"},
    )
    assert response.status_code == 200
    body = response.json()
    total = body["prob_home_win"] + body["prob_draw"] + body["prob_away_win"]
    assert abs(total - 1.0) < 1e-6
    assert body["expected_home_goals"] >= 0


def test_predict_api_same_team(data_client: TestClient) -> None:
    response = data_client.post(
        "/predictions/match",
        json={"home_team_id": "T-BRA", "away_team_id": "T-BRA"},
    )
    assert response.status_code == 422


def test_predict_api_unknown_team(data_client: TestClient) -> None:
    response = data_client.post(
        "/predictions/match",
        json={"home_team_id": "T-BRA", "away_team_id": "nope"},
    )
    assert response.status_code == 404


