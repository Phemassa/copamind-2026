"""Modelo Poisson / Dixon-Coles (MASTER_PLAN §16.2)."""

from copamind.models.poisson.dixon_coles import (
    MatchPrediction,
    PoissonConfig,
    PoissonModel,
    poisson_pmf,
)

__all__ = ["MatchPrediction", "PoissonConfig", "PoissonModel", "poisson_pmf"]
