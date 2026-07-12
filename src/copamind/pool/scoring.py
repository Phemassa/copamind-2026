"""Pontuação do bolão (MASTER_PLAN §37.10).

Duas dimensões: pontos de bolão (sistema de estrelas) e qualidade
probabilística (Brier score sobre o desfecho 1x2).

Sistema de estrelas (espelha starRating em app.js):
  ★     vencedor certo                         = 3 pts
  ★★    vencedor + 1 gol certo                 = 4 pts
  ★★★   placar exato                           = 5 pts
  ★★★★  + tempo correto (normal/ET/pen)        = 6 pts  [requer pick_payload]
  ★★★★★ + vencedor nos pênaltis               = 7 pts  [requer pick_payload]
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Outcome = Literal["home", "draw", "away"]

POINTS_EXACT_SCORE = 5
POINTS_CORRECT_RESULT = 3
POINTS_ONE_GOAL_RIGHT = 4  # vencedor + 1 gol certo
POINTS_TIME_RIGHT = 6      # placar exato + formato de tempo correto
POINTS_PERFECT = 7         # tudo certo (inclui pênaltis se aplicável)


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
    """Pontos de bolão sem dados de tempo extra (stars 1-3 only).

    Usa pelo menos os três primeiros níveis do sistema de estrelas:
    - placar exato          = 5 pts (★★★)
    - vencedor + 1 gol certo = 4 pts (★★)
    - apenas vencedor certo = 3 pts (★)
    - errou o vencedor      = 0 pts
    """
    pred_outcome = outcome(predicted_home, predicted_away)
    actual_outcome = outcome(actual_home, actual_away)
    if pred_outcome != actual_outcome:
        return 0
    # placar exato → 5 pts (★★★)
    if predicted_home == actual_home and predicted_away == actual_away:
        return POINTS_EXACT_SCORE
    # vencedor + pelo menos 1 gol certo → 4 pts (★★)
    home_right = predicted_home == actual_home
    away_right = predicted_away == actual_away
    if home_right or away_right:
        return POINTS_ONE_GOAL_RIGHT
    # apenas vencedor → 3 pts (★)
    return POINTS_CORRECT_RESULT


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
