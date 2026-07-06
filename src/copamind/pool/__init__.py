"""Bolão de IAs Locais (E11, MASTER_PLAN §37.10)."""

from copamind.pool.predictors import (
    EloPredictor,
    LLMPredictor,
    PoissonPredictor,
    Predictor,
    default_predictors,
)
from copamind.pool.scoring import ScoredPrediction, bolao_points, brier_score, outcome
from copamind.pool.service import (
    PredictorStanding,
    leaderboard,
    run_backtest,
    score_all,
)

__all__ = [
    "EloPredictor",
    "LLMPredictor",
    "PoissonPredictor",
    "Predictor",
    "PredictorStanding",
    "ScoredPrediction",
    "bolao_points",
    "brier_score",
    "default_predictors",
    "leaderboard",
    "outcome",
    "run_backtest",
    "score_all",
]
