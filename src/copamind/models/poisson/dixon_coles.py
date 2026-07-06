"""Modelo de gols Poisson com correção opcional de Dixon-Coles (MASTER_PLAN §16.2).

As forças de ataque e defesa são estimadas de forma fechada (razões em relação
à média da liga), sem otimização numérica — o que mantém o modelo determinístico
e sem dependência de SciPy. A partir das taxas esperadas de gols constrói-se a
matriz de placares e as probabilidades de vitória/empate/derrota (soma ≈ 1).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from pydantic import BaseModel, Field

from copamind.data.schemas import Match, MatchStatus

_EPS = 1e-9


class PoissonConfig(BaseModel):
    """Parâmetros do modelo Poisson/Dixon-Coles."""

    max_goals: int = Field(default=10, ge=1, le=20)
    use_dixon_coles: bool = True
    rho: float = Field(default=-0.05, ge=-1.0, le=1.0)


class MatchPrediction(BaseModel):
    """Resultado da previsão de uma partida."""

    home_team_id: str
    away_team_id: str
    expected_home_goals: float = Field(ge=0)
    expected_away_goals: float = Field(ge=0)
    prob_home_win: float = Field(ge=0, le=1)
    prob_draw: float = Field(ge=0, le=1)
    prob_away_win: float = Field(ge=0, le=1)
    prob_over_2_5: float = Field(ge=0, le=1)
    most_likely_score: tuple[int, int]


def poisson_pmf(k: int, lam: float) -> float:
    """Função de massa de Poisson: P(X=k) para média ``lam``."""
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return math.exp(-lam) * lam**k / math.factorial(k)


def _dixon_coles_tau(i: int, j: int, lam_home: float, lam_away: float, rho: float) -> float:
    """Correção de baixos placares de Dixon-Coles."""
    if i == 0 and j == 0:
        return 1.0 - lam_home * lam_away * rho
    if i == 0 and j == 1:
        return 1.0 + lam_home * rho
    if i == 1 and j == 0:
        return 1.0 + lam_away * rho
    if i == 1 and j == 1:
        return 1.0 - rho
    return 1.0


@dataclass
class PoissonModel:
    """Modelo de força ofensiva/defensiva por seleção."""

    config: PoissonConfig = field(default_factory=PoissonConfig)
    _attack: dict[str, float] = field(default_factory=dict, init=False)
    _defense: dict[str, float] = field(default_factory=dict, init=False)
    _avg_home_goals: float = field(default=1.3, init=False)
    _avg_away_goals: float = field(default=1.1, init=False)
    _fitted: bool = field(default=False, init=False)

    def fit(self, matches: list[Match]) -> None:
        """Estima as forças a partir de partidas finalizadas com placar."""
        finished = [
            m
            for m in matches
            if m.status is MatchStatus.finished
            and m.home_score is not None
            and m.away_score is not None
        ]
        if not finished:
            raise ValueError("é necessário ao menos uma partida finalizada")

        total_home = sum(m.home_score for m in finished if m.home_score is not None)
        total_away = sum(m.away_score for m in finished if m.away_score is not None)
        n = len(finished)
        self._avg_home_goals = total_home / n
        self._avg_away_goals = total_away / n

        scored: dict[str, int] = {}
        conceded: dict[str, int] = {}
        games: dict[str, int] = {}
        for m in finished:
            assert m.home_score is not None and m.away_score is not None
            for team, gf, ga in (
                (m.home_team_id, m.home_score, m.away_score),
                (m.away_team_id, m.away_score, m.home_score),
            ):
                scored[team] = scored.get(team, 0) + gf
                conceded[team] = conceded.get(team, 0) + ga
                games[team] = games.get(team, 0) + 1

        overall_avg = (total_home + total_away) / (2 * n)
        overall_avg = max(overall_avg, _EPS)

        self._attack = {team: (scored[team] / games[team]) / overall_avg for team in games}
        self._defense = {team: (conceded[team] / games[team]) / overall_avg for team in games}
        self._fitted = True

    def _strength(self, mapping: dict[str, float], team_id: str) -> float:
        return mapping.get(team_id, 1.0)

    def attack_strength(self, team_id: str) -> float:
        """Força ofensiva relativa da seleção (1.0 = média da liga)."""
        return self._strength(self._attack, team_id)

    def defense_strength(self, team_id: str) -> float:
        """Fragilidade defensiva relativa (>1 concede mais que a média)."""
        return self._strength(self._defense, team_id)

    def expected_goals(
        self, home_id: str, away_id: str, *, neutral_venue: bool = False
    ) -> tuple[float, float]:
        """Taxas esperadas de gols (mandante, visitante)."""
        home_base = self._avg_home_goals
        away_base = self._avg_away_goals
        if neutral_venue:
            neutral = (self._avg_home_goals + self._avg_away_goals) / 2.0
            home_base = away_base = neutral
        lam_home = (
            home_base
            * self._strength(self._attack, home_id)
            * self._strength(self._defense, away_id)
        )
        lam_away = (
            away_base
            * self._strength(self._attack, away_id)
            * self._strength(self._defense, home_id)
        )
        return max(lam_home, _EPS), max(lam_away, _EPS)

    def score_matrix(self, lam_home: float, lam_away: float) -> list[list[float]]:
        """Matriz de probabilidades de placar, normalizada (soma = 1)."""
        size = self.config.max_goals + 1
        matrix = [[0.0] * size for _ in range(size)]
        total = 0.0
        for i in range(size):
            p_i = poisson_pmf(i, lam_home)
            for j in range(size):
                cell = p_i * poisson_pmf(j, lam_away)
                if self.config.use_dixon_coles:
                    cell *= _dixon_coles_tau(i, j, lam_home, lam_away, self.config.rho)
                cell = max(cell, 0.0)
                matrix[i][j] = cell
                total += cell
        if total > 0:
            for i in range(size):
                for j in range(size):
                    matrix[i][j] /= total
        return matrix

    def predict_match(
        self, home_id: str, away_id: str, *, neutral_venue: bool = False
    ) -> MatchPrediction:
        """Prediz probabilidades 1x2, gols esperados e placar mais provável."""
        if not self._fitted:
            raise ValueError("o modelo precisa ser ajustado com fit() antes de prever")
        lam_home, lam_away = self.expected_goals(home_id, away_id, neutral_venue=neutral_venue)
        matrix = self.score_matrix(lam_home, lam_away)
        size = self.config.max_goals + 1

        prob_home = prob_draw = prob_away = prob_over = 0.0
        best_score = (0, 0)
        best_prob = -1.0
        for i in range(size):
            for j in range(size):
                p = matrix[i][j]
                if i > j:
                    prob_home += p
                elif i == j:
                    prob_draw += p
                else:
                    prob_away += p
                if i + j > 2:
                    prob_over += p
                if p > best_prob:
                    best_prob = p
                    best_score = (i, j)

        return MatchPrediction(
            home_team_id=home_id,
            away_team_id=away_id,
            expected_home_goals=lam_home,
            expected_away_goals=lam_away,
            prob_home_win=prob_home,
            prob_draw=prob_draw,
            prob_away_win=prob_away,
            prob_over_2_5=prob_over,
            most_likely_score=best_score,
        )
