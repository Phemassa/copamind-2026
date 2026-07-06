"""Métricas de calibração: Brier, Log Loss, ECE e curva de confiabilidade."""

from __future__ import annotations

import math

from pydantic import BaseModel

ProbTriple = tuple[float, float, float]
_EPS = 1e-12


def brier_multiclass(probs: list[ProbTriple], outcomes: list[int]) -> float:
    """Brier score multiclasse médio (0 = perfeito)."""
    if len(probs) != len(outcomes):
        raise ValueError("probs e outcomes devem ter o mesmo tamanho")
    if not probs:
        return 0.0
    total = 0.0
    for triple, outcome in zip(probs, outcomes, strict=True):
        target = [0.0, 0.0, 0.0]
        target[outcome] = 1.0
        total += sum((triple[i] - target[i]) ** 2 for i in range(3))
    return total / len(probs)


def multiclass_log_loss(probs: list[ProbTriple], outcomes: list[int]) -> float:
    """Log loss multiclasse médio (menor é melhor)."""
    if len(probs) != len(outcomes):
        raise ValueError("probs e outcomes devem ter o mesmo tamanho")
    if not probs:
        return 0.0
    total = 0.0
    for triple, outcome in zip(probs, outcomes, strict=True):
        p = min(max(triple[outcome], _EPS), 1.0)
        total += -math.log(p)
    return total / len(probs)


class ReliabilityBin(BaseModel):
    """Faixa da curva de confiabilidade."""

    lower: float
    upper: float
    count: int
    avg_confidence: float
    accuracy: float


def _confidence_and_correct(
    probs: list[ProbTriple], outcomes: list[int]
) -> tuple[list[float], list[bool]]:
    confidences: list[float] = []
    correct: list[bool] = []
    for triple, outcome in zip(probs, outcomes, strict=True):
        predicted = max(range(3), key=lambda i: triple[i])
        confidences.append(triple[predicted])
        correct.append(predicted == outcome)
    return confidences, correct


def reliability_curve(
    probs: list[ProbTriple], outcomes: list[int], *, n_bins: int = 10
) -> list[ReliabilityBin]:
    """Curva de confiabilidade (confiança prevista vs acurácia observada)."""
    confidences, correct = _confidence_and_correct(probs, outcomes)
    bins: list[ReliabilityBin] = []
    for b in range(n_bins):
        lower = b / n_bins
        upper = (b + 1) / n_bins
        indices = [
            i
            for i, c in enumerate(confidences)
            if (c > lower or (b == 0 and c >= lower)) and c <= upper
        ]
        count = len(indices)
        if count == 0:
            bins.append(
                ReliabilityBin(lower=lower, upper=upper, count=0, avg_confidence=0.0, accuracy=0.0)
            )
            continue
        avg_conf = sum(confidences[i] for i in indices) / count
        acc = sum(1 for i in indices if correct[i]) / count
        bins.append(
            ReliabilityBin(
                lower=lower, upper=upper, count=count, avg_confidence=avg_conf, accuracy=acc
            )
        )
    return bins


def expected_calibration_error(
    probs: list[ProbTriple], outcomes: list[int], *, n_bins: int = 10
) -> float:
    """Expected Calibration Error (ECE): média ponderada |acurácia - confiança|."""
    if not probs:
        return 0.0
    bins = reliability_curve(probs, outcomes, n_bins=n_bins)
    total = len(probs)
    return sum((b.count / total) * abs(b.accuracy - b.avg_confidence) for b in bins if b.count)
