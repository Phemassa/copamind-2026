"""Serviço de ensemble: combina Elo e Poisson em uma previsão 1x2."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from copamind.data.repositories import DuckDBRepository
from copamind.features.service import build_elo
from copamind.models.ensemble.blend import EnsembleConfig, ProbTriple, blend_named
from copamind.models.poisson.service import build_poisson

# Peso default do ensemble (ajustável / aprendível em validação temporal).
DEFAULT_ENSEMBLE = EnsembleConfig(weights={"elo": 0.4, "poisson": 0.6})
_ELO_DRAW_PROBABILITY = 0.26


class EnsemblePrediction(BaseModel):
    """Previsão 1x2 do ensemble."""

    home_team_id: str
    away_team_id: str
    prob_home: float
    prob_draw: float
    prob_away: float


def _elo_triple(
    repo: DuckDBRepository, home: str, away: str, *, neutral: bool, as_of: datetime | None
) -> ProbTriple:
    elo = build_elo(repo, as_of=as_of)
    expected_home = elo.win_probability(home, away, neutral_venue=neutral)
    non_draw = 1.0 - _ELO_DRAW_PROBABILITY
    return (non_draw * expected_home, _ELO_DRAW_PROBABILITY, non_draw * (1.0 - expected_home))


def ensemble_match(
    repo: DuckDBRepository,
    home: str,
    away: str,
    *,
    neutral_venue: bool = False,
    config: EnsembleConfig | None = None,
    as_of: datetime | None = None,
) -> EnsemblePrediction:
    """Combina Elo e Poisson em uma previsão calibrável de 1x2."""
    config = config or DEFAULT_ENSEMBLE
    poisson = build_poisson(repo, as_of=as_of)
    poisson_pred = poisson.predict_match(home, away, neutral_venue=neutral_venue)
    poisson_triple: ProbTriple = (
        poisson_pred.prob_home_win,
        poisson_pred.prob_draw,
        poisson_pred.prob_away_win,
    )
    elo_triple = _elo_triple(repo, home, away, neutral=neutral_venue, as_of=as_of)
    home_p, draw_p, away_p = blend_named({"elo": elo_triple, "poisson": poisson_triple}, config)
    return EnsemblePrediction(
        home_team_id=home,
        away_team_id=away,
        prob_home=home_p,
        prob_draw=draw_p,
        prob_away=away_p,
    )
