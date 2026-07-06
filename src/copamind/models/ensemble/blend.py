"""Combinação (blend) de probabilidades 1x2 de múltiplos modelos.

Os pesos podem ser configurados ou selecionados em validação temporal
minimizando o Brier (MASTER_PLAN §16.5, §37.5).
"""

from __future__ import annotations

from pydantic import BaseModel, Field

# (home, draw, away)
ProbTriple = tuple[float, float, float]


class EnsembleConfig(BaseModel):
    """Pesos por modelo no ensemble."""

    weights: dict[str, float] = Field(default_factory=dict)


def blend(probs: list[ProbTriple], weights: list[float]) -> ProbTriple:
    """Combina triplas 1x2 por média ponderada, normalizada para somar 1."""
    if not probs:
        raise ValueError("é necessário ao menos uma tripla de probabilidades")
    if len(probs) != len(weights):
        raise ValueError("probs e weights devem ter o mesmo tamanho")
    combined = [0.0, 0.0, 0.0]
    for triple, weight in zip(probs, weights, strict=True):
        for i in range(3):
            combined[i] += weight * triple[i]
    total = sum(combined)
    if total <= 0:
        return (1 / 3, 1 / 3, 1 / 3)
    return (combined[0] / total, combined[1] / total, combined[2] / total)


def blend_named(named: dict[str, ProbTriple], config: EnsembleConfig) -> ProbTriple:
    """Combina probabilidades nomeadas usando os pesos da configuração."""
    probs: list[ProbTriple] = []
    weights: list[float] = []
    for name, triple in named.items():
        weight = config.weights.get(name, 0.0)
        if weight > 0:
            probs.append(triple)
            weights.append(weight)
    if not probs:
        # Sem pesos aplicáveis: média simples.
        values = list(named.values())
        return blend(values, [1.0] * len(values))
    return blend(probs, weights)


def _brier(triple: ProbTriple, outcome_index: int) -> float:
    target = [0.0, 0.0, 0.0]
    target[outcome_index] = 1.0
    return sum((triple[i] - target[i]) ** 2 for i in range(3))


def fit_two_model_weights(
    model_a: list[ProbTriple],
    model_b: list[ProbTriple],
    outcomes: list[int],
    *,
    steps: int = 11,
) -> tuple[float, float]:
    """Seleciona (peso_a, peso_b) que minimiza o Brier médio (busca em grade).

    ``outcomes`` são índices 0=home, 1=draw, 2=away.
    """
    if not (len(model_a) == len(model_b) == len(outcomes)):
        raise ValueError("entradas devem ter o mesmo tamanho")
    best = (0.5, 0.5)
    best_brier = float("inf")
    for i in range(steps):
        wa = i / (steps - 1)
        wb = 1.0 - wa
        total = 0.0
        for pa, pb, outcome in zip(model_a, model_b, outcomes, strict=True):
            blended = blend([pa, pb], [wa, wb])
            total += _brier(blended, outcome)
        mean_brier = total / len(outcomes)
        if mean_brier < best_brier:
            best_brier = mean_brier
            best = (wa, wb)
    return best
