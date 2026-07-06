"""Testes de ensemble e calibração."""

from __future__ import annotations

import pytest

from copamind.models.calibration.isotonic import CalibratedTriples, IsotonicCalibrator
from copamind.models.calibration.metrics import (
    brier_multiclass,
    expected_calibration_error,
    multiclass_log_loss,
    reliability_curve,
)
from copamind.models.ensemble.blend import (
    EnsembleConfig,
    blend,
    blend_named,
    fit_two_model_weights,
)


def test_blend_normalizes() -> None:
    result = blend([(0.6, 0.2, 0.2), (0.4, 0.4, 0.2)], [1.0, 1.0])
    assert sum(result) == pytest.approx(1.0)
    assert result[0] > result[2]


def test_blend_named_uses_weights() -> None:
    config = EnsembleConfig(weights={"elo": 0.0, "poisson": 1.0})
    result = blend_named({"elo": (1.0, 0.0, 0.0), "poisson": (0.0, 0.0, 1.0)}, config)
    assert result[2] == pytest.approx(1.0)


def test_fit_two_model_weights_prefers_better_model() -> None:
    # model_a sempre certo (home), model_b sempre errado.
    model_a = [(0.9, 0.05, 0.05)] * 10
    model_b = [(0.05, 0.05, 0.9)] * 10
    outcomes = [0] * 10
    wa, wb = fit_two_model_weights(model_a, model_b, outcomes)
    assert wa > wb


def test_brier_and_logloss() -> None:
    probs = [(1.0, 0.0, 0.0)]
    assert brier_multiclass(probs, [0]) == pytest.approx(0.0)
    assert multiclass_log_loss(probs, [0]) == pytest.approx(0.0, abs=1e-6)


def test_reliability_curve_bins() -> None:
    probs = [(0.9, 0.05, 0.05), (0.9, 0.05, 0.05)]
    outcomes = [0, 2]  # um certo, um errado -> acurácia 0.5 na faixa alta
    bins = reliability_curve(probs, outcomes, n_bins=10)
    high = [b for b in bins if b.count > 0][-1]
    assert high.count == 2
    assert high.accuracy == pytest.approx(0.5)


def test_ece_detects_overconfidence() -> None:
    probs = [(0.95, 0.03, 0.02)] * 10
    outcomes = [0] * 5 + [2] * 5  # só 50% de acerto, mas confiança 95%
    assert expected_calibration_error(probs, outcomes) > 0.4


def test_isotonic_calibrator_monotone() -> None:
    cal = IsotonicCalibrator().fit([0.1, 0.4, 0.35, 0.8], [0, 0, 1, 1])
    assert cal.predict(0.1) <= cal.predict(0.8)


def test_calibrated_triples_valid_and_reduces_ece() -> None:
    # Modelo superconfiante: prevê 0.9 home mas só metade acontece.
    probs = [(0.9, 0.05, 0.05)] * 10
    outcomes = [0] * 5 + [1] * 5
    cal = CalibratedTriples().fit(probs, outcomes)
    calibrated = [cal.transform(p) for p in probs]
    for triple in calibrated:
        assert sum(triple) == pytest.approx(1.0)
    ece_before = expected_calibration_error(probs, outcomes)
    ece_after = expected_calibration_error(calibrated, outcomes)
    assert ece_after <= ece_before
