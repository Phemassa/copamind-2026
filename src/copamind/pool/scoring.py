"""Pontuação do bolão (MASTER_PLAN §37.10).

Duas dimensões: pontos de bolão (placar exato / resultado correto) e qualidade
probabilística (Brier score sobre o desfecho 1x2).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Outcome = Literal["home", "draw", "away"]

POINTS_EXACT_SCORE = 5
POINTS_CORRECT_RESULT = 3


def outcome(home_score: int, away_score: int) -> Outcome:
    """Desfecho de uma partida a partir do placar."""
    if home_score > away_score:
        return "home"
    if home_score < away_score:
        return "away"
    return "draw"


def bolao_points(
    predicted_home: int,
    predicted_away: int,
    actual_home: int,
    actual_away: int,
) -> int:
    """Pontos de bolão: placar exato = 5, resultado correto = 3, caso contrário 0."""
    if predicted_home == actual_home and predicted_away == actual_away:
        return POINTS_EXACT_SCORE
    if outcome(predicted_home, predicted_away) == outcome(actual_home, actual_away):
        return POINTS_CORRECT_RESULT
    return 0


def brier_score(
    prob_home: float,
    prob_draw: float,
    prob_away: float,
    actual: Outcome,
) -> float:
    """Brier score multiclasse (0 = perfeito, 2 = pior) para o desfecho 1x2."""
    target = {
        "home": (1.0, 0.0, 0.0),
        "draw": (0.0, 1.0, 0.0),
        "away": (0.0, 0.0, 1.0),
    }[actual]
    probs = (prob_home, prob_draw, prob_away)
    return sum((p - t) ** 2 for p, t in zip(probs, target, strict=True))


class ScoredPrediction(BaseModel):
    """Palpite avaliado contra o resultado real."""

    predictor_name: str
    match_id: str
    points: int = Field(ge=0)
    brier: float = Field(ge=0, le=2)
    correct_result: bool
    exact_score: bool
