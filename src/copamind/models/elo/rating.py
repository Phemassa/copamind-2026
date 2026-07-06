"""Rating Elo para seleções (MASTER_PLAN §16.1).

Determinístico: dado o mesmo conjunto de partidas e configuração, produz
sempre os mesmos ratings. As partidas são processadas em ordem cronológica
(``match_date``, desempate por ``match_id``), evitando dependência da ordem
de entrada. Não há vazamento temporal: só partidas finalizadas entram, e o
chamador pode restringir por ``available_at`` na origem dos dados.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from pydantic import BaseModel, Field

from copamind.data.schemas import Match, MatchStatus


class EloConfig(BaseModel):
    """Parâmetros do sistema Elo."""

    base_rating: float = Field(default=1500.0, gt=0)
    k_factor: float = Field(default=32.0, gt=0)
    home_advantage: float = Field(default=65.0, ge=0)
    use_goal_difference: bool = True


@dataclass(frozen=True)
class RatingChange:
    """Registro de alteração de rating em uma partida."""

    match_id: str
    team_id: str
    opponent_id: str
    match_date: datetime
    rating_before: float
    rating_after: float
    expected_score: float
    actual_score: float


def expected_score(rating_a: float, rating_b: float) -> float:
    """Pontuação esperada de A contra B (0..1) pela fórmula logística do Elo."""
    result: float = 1.0 / (1.0 + 10.0 ** ((rating_b - rating_a) / 400.0))
    return result


def goal_difference_multiplier(goal_difference: int) -> float:
    """Multiplicador do K conforme a diferença de gols (estilo World Football Elo)."""
    diff = abs(goal_difference)
    if diff <= 1:
        return 1.0
    if diff == 2:
        return 1.5
    return (11.0 + diff) / 8.0


def _actual_score(home_score: int, away_score: int) -> float:
    if home_score > away_score:
        return 1.0
    if home_score == away_score:
        return 0.5
    return 0.0


@dataclass
class EloRatingSystem:
    """Mantém e atualiza ratings Elo a partir de partidas finalizadas."""

    config: EloConfig = field(default_factory=EloConfig)
    _ratings: dict[str, float] = field(default_factory=dict, init=False)
    history: list[RatingChange] = field(default_factory=list, init=False)

    def rating(self, team_id: str) -> float:
        """Rating atual de uma seleção (``base_rating`` se desconhecida)."""
        return self._ratings.get(team_id, self.config.base_rating)

    def ratings(self) -> dict[str, float]:
        """Cópia do mapa atual de ratings."""
        return dict(self._ratings)

    def win_probability(self, home_id: str, away_id: str, *, neutral_venue: bool = False) -> float:
        """Probabilidade esperada (escalar) do mandante, incluindo vantagem de campo.

        Observação: o split vitória/empate/derrota adequado é responsabilidade
        do modelo de Poisson (E4); aqui é apenas a pontuação esperada do Elo.
        """
        advantage = 0.0 if neutral_venue else self.config.home_advantage
        return expected_score(self.rating(home_id) + advantage, self.rating(away_id))

    def process_match(self, match: Match) -> None:
        """Atualiza os ratings das duas seleções com base em uma partida."""
        if match.status is not MatchStatus.finished:
            raise ValueError("Elo só processa partidas finalizadas")
        if match.home_score is None or match.away_score is None:
            raise ValueError("partida finalizada sem placar")

        home_rating = self.rating(match.home_team_id)
        away_rating = self.rating(match.away_team_id)

        advantage = 0.0 if match.neutral_venue else self.config.home_advantage
        expected_home = expected_score(home_rating + advantage, away_rating)
        actual_home = _actual_score(match.home_score, match.away_score)

        multiplier = (
            goal_difference_multiplier(match.home_score - match.away_score)
            if self.config.use_goal_difference
            else 1.0
        )
        k_effective = self.config.k_factor * multiplier * match.importance_weight
        delta = k_effective * (actual_home - expected_home)

        self._ratings[match.home_team_id] = home_rating + delta
        self._ratings[match.away_team_id] = away_rating - delta

        self.history.append(
            RatingChange(
                match_id=match.match_id,
                team_id=match.home_team_id,
                opponent_id=match.away_team_id,
                match_date=match.match_date,
                rating_before=home_rating,
                rating_after=home_rating + delta,
                expected_score=expected_home,
                actual_score=actual_home,
            )
        )
        self.history.append(
            RatingChange(
                match_id=match.match_id,
                team_id=match.away_team_id,
                opponent_id=match.home_team_id,
                match_date=match.match_date,
                rating_before=away_rating,
                rating_after=away_rating - delta,
                expected_score=1.0 - expected_home,
                actual_score=1.0 - actual_home,
            )
        )

    def process_matches(self, matches: list[Match]) -> None:
        """Processa uma lista de partidas em ordem cronológica determinística."""
        ordered = sorted(matches, key=lambda m: (m.match_date, m.match_id))
        for match in ordered:
            self.process_match(match)
