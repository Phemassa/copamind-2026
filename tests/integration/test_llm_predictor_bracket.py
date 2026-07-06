"""Testes do LLMPredictor no bolão e do helper de bracket."""

from __future__ import annotations

import json

from copamind.data.repositories import DuckDBRepository
from copamind.llm.client import FakeLLMClient
from copamind.pool.predictors import LLMPredictor
from copamind.pool.service import run_backtest
from copamind.ui.dashboard import stage_probabilities_view


def _pick_json() -> str:
    return json.dumps(
        {
            "prob_home": 0.5,
            "prob_draw": 0.3,
            "prob_away": 0.2,
            "predicted_home_goals": 2,
            "predicted_away_goals": 1,
        }
    )


def test_llm_predictor_produces_pick(seeded_repo: DuckDBRepository) -> None:
    client = FakeLLMClient({"analyst": _pick_json()})
    predictor = LLMPredictor(client, "analyst", name="llm:test")
    matches = seeded_repo.list_finished_matches()
    target = matches[-1]  # histórico suficiente
    data = predictor.predict(seeded_repo, target)
    assert data is not None
    assert abs(data.prob_home + data.prob_draw + data.prob_away - 1.0) < 1e-6
    assert data.predicted_home_goals == 2


def test_llm_predictor_in_backtest(seeded_repo: DuckDBRepository) -> None:
    client = FakeLLMClient({"analyst": _pick_json()})
    predictors = [LLMPredictor(client, "analyst", name="llm:test")]
    summary = run_backtest(seeded_repo, predictors)
    assert summary.predictions_locked > 0
    assert any(s.predictor_name == "llm:test" for s in summary.standings)


def test_llm_predictor_handles_bad_output(seeded_repo: DuckDBRepository) -> None:
    client = FakeLLMClient({"analyst": "isto não é json"})
    predictor = LLMPredictor(client, "analyst")
    matches = seeded_repo.list_finished_matches()
    # Saída inválida -> None (não trava palpite).
    assert predictor.predict(seeded_repo, matches[-1]) is None


def test_stage_probabilities_view(seeded_repo: DuckDBRepository) -> None:
    rows = stage_probabilities_view(seeded_repo, iterations=500)
    assert len(rows) == 4
    for row in rows:
        assert "team_id" in row
        assert "champion" in row
