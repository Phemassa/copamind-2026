"""Calibração de probabilidades (MASTER_PLAN §16.6)."""

from copamind.models.calibration.isotonic import CalibratedTriples, IsotonicCalibrator
from copamind.models.calibration.metrics import (
    ReliabilityBin,
    brier_multiclass,
    expected_calibration_error,
    multiclass_log_loss,
    reliability_curve,
)

__all__ = [
    "CalibratedTriples",
    "IsotonicCalibrator",
    "ReliabilityBin",
    "brier_multiclass",
    "expected_calibration_error",
    "multiclass_log_loss",
    "reliability_curve",
]
