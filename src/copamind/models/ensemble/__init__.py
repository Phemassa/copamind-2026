"""Ensemble de probabilidades (MASTER_PLAN §16.5)."""

from copamind.models.ensemble.blend import (
    EnsembleConfig,
    ProbTriple,
    blend,
    fit_two_model_weights,
)

__all__ = ["EnsembleConfig", "ProbTriple", "blend", "fit_two_model_weights"]
