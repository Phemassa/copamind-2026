"""Preditores do bolão.

Cada preditor é uma "IA" que gera, para uma partida, probabilidades 1x2 e um
placar previsto — usando apenas dados disponíveis antes do apito (anti-leakage).
Novos preditores (LLMs locais) serão plugados aqui no E7.
"""

from __future__ import annotations

from typing import Protocol

from copamind.data.repositories import DuckDBRepository
from copamind.data.schemas import Match
from copamind.features.service import build_elo
from copamind.models.poisson.service import build_poisson

# Histórico mínimo (partidas) para um preditor produzir palpite confiável.
MIN_HISTORY = 3

ELO_DRAW_PROBABILITY = 0.26


class PoolPredictionData:
    """Saída de um preditor: probabilidades e placar previsto."""

    def __init__(
        self,
        prob_home: float,
        prob_draw: float,
        prob_away: float,
        predicted_home_goals: int,
        predicted_away_goals: int,
    ) -> None:
        self.prob_home = prob_home
        self.prob_draw = prob_draw
        self.prob_away = prob_away
        self.predicted_home_goals = predicted_home_goals
        self.predicted_away_goals = predicted_away_goals


class Predictor(Protocol):
    """Interface de um preditor do bolão."""

    name: str

    def predict(self, repo: DuckDBRepository, match: Match) -> PoolPredictionData | None:
        """Produz um palpite ou ``None`` se não houver histórico suficiente."""
        ...


class PoissonPredictor:
    """Preditor baseado no modelo Poisson/Dixon-Coles."""

    name = "poisson"

    def predict(self, repo: DuckDBRepository, match: Match) -> PoolPredictionData | None:
        history = repo.list_finished_matches(as_of=match.match_date)
        if len(history) < MIN_HISTORY:
            return None
        model = build_poisson(repo, as_of=match.match_date)
        pred = model.predict_match(
            match.home_team_id, match.away_team_id, neutral_venue=match.neutral_venue
        )
        return PoolPredictionData(
            prob_home=pred.prob_home_win,
            prob_draw=pred.prob_draw,
            prob_away=pred.prob_away_win,
            predicted_home_goals=pred.most_likely_score[0],
            predicted_away_goals=pred.most_likely_score[1],
        )


class EloPredictor:
    """Preditor baseado no rating Elo (com probabilidade de empate fixa)."""

    name = "elo"

    def predict(self, repo: DuckDBRepository, match: Match) -> PoolPredictionData | None:
        history = repo.list_finished_matches(as_of=match.match_date)
        if len(history) < MIN_HISTORY:
            return None
        elo = build_elo(repo, as_of=match.match_date)
        expected_home = elo.win_probability(
            match.home_team_id, match.away_team_id, neutral_venue=match.neutral_venue
        )
        non_draw = 1.0 - ELO_DRAW_PROBABILITY
        prob_home = non_draw * expected_home
        prob_away = non_draw * (1.0 - expected_home)
        if expected_home > 0.5:
            score = (1, 0)
        elif expected_home < 0.5:
            score = (0, 1)
        else:
            score = (1, 1)
        return PoolPredictionData(
            prob_home=prob_home,
            prob_draw=ELO_DRAW_PROBABILITY,
            prob_away=prob_away,
            predicted_home_goals=score[0],
            predicted_away_goals=score[1],
        )


def default_predictors() -> list[Predictor]:
    """Preditores padrão do bolão (LLMs entram no E7)."""
    return [PoissonPredictor(), EloPredictor()]
