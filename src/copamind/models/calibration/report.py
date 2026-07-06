"""Relatório de calibração a partir dos palpites do bolão (E11 + E3b)."""

from __future__ import annotations

from pydantic import BaseModel

from copamind.data.repositories import DuckDBRepository
from copamind.models.calibration.metrics import (
    ReliabilityBin,
    brier_multiclass,
    expected_calibration_error,
    multiclass_log_loss,
    reliability_curve,
)
from copamind.pool.scoring import outcome

_OUTCOME_INDEX = {"home": 0, "draw": 1, "away": 2}


class CalibrationReport(BaseModel):
    """Métricas de calibração de um preditor."""

    predictor_name: str
    samples: int
    brier: float
    log_loss: float
    ece: float
    reliability: list[ReliabilityBin]


def calibration_report(repo: DuckDBRepository) -> list[CalibrationReport]:
    """Calcula Brier/LogLoss/ECE e curva de confiabilidade por preditor."""
    results = {r.match_id: r for r in repo.list_pool_results()}
    grouped: dict[str, tuple[list[tuple[float, float, float]], list[int]]] = {}
    for pred in repo.list_pool_predictions():
        result = results.get(pred.match_id)
        if result is None:
            continue
        index = _OUTCOME_INDEX[outcome(result.home_score, result.away_score)]
        probs, outcomes = grouped.setdefault(pred.predictor_name, ([], []))
        probs.append((pred.prob_home, pred.prob_draw, pred.prob_away))
        outcomes.append(index)

    reports: list[CalibrationReport] = []
    for name, (probs, outcomes) in grouped.items():
        reports.append(
            CalibrationReport(
                predictor_name=name,
                samples=len(probs),
                brier=brier_multiclass(probs, outcomes),
                log_loss=multiclass_log_loss(probs, outcomes),
                ece=expected_calibration_error(probs, outcomes),
                reliability=reliability_curve(probs, outcomes),
            )
        )
    reports.sort(key=lambda r: r.brier)
    return reports
