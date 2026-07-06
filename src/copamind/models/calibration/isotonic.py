"""Calibração isotônica via Pool Adjacent Violators (PAV), sem dependências pesadas.

Ajusta uma função monótona não decrescente que mapeia probabilidade prevista em
probabilidade calibrada. Para o caso 1x2, calibra cada classe e renormaliza.
"""

from __future__ import annotations

ProbTriple = tuple[float, float, float]


def _pav(values: list[float], weights: list[float]) -> list[float]:
    """Pool Adjacent Violators: ajuste isotônico (não decrescente).

    Retorna um valor ajustado por posição de entrada (aligned a ``values``).
    """
    # Cada bloco: [soma_ponderada, peso, n_posicoes, valor_medio].
    blocks: list[list[float]] = []
    for value, weight in zip(values, weights, strict=True):
        blocks.append([value * weight, weight, 1.0, value])
        while len(blocks) > 1 and blocks[-2][3] > blocks[-1][3]:
            last = blocks.pop()
            prev = blocks.pop()
            wsum = prev[0] + last[0]
            weight_total = prev[1] + last[1]
            positions = prev[2] + last[2]
            blocks.append([wsum, weight_total, positions, wsum / weight_total])
    result: list[float] = []
    for block in blocks:
        result.extend([block[3]] * round(block[2]))
    return result


class IsotonicCalibrator:
    """Calibrador isotônico 1D (probabilidade prevista -> calibrada)."""

    def __init__(self) -> None:
        self._x: list[float] = []
        self._y: list[float] = []
        self._fitted = False

    def fit(self, predictions: list[float], labels: list[int]) -> IsotonicCalibrator:
        """Ajusta usando probabilidades previstas e rótulos binários (0/1)."""
        if len(predictions) != len(labels):
            raise ValueError("predictions e labels devem ter o mesmo tamanho")
        if not predictions:
            raise ValueError("é necessário ao menos um exemplo")
        order = sorted(range(len(predictions)), key=lambda i: predictions[i])
        # Agrupa previsões empatadas (a regressão isotônica com x iguais deve
        # usar a média dos rótulos, ponderada pela contagem).
        xs: list[float] = []
        means: list[float] = []
        weights: list[float] = []
        for i in order:
            x = predictions[i]
            if xs and xs[-1] == x:
                total = means[-1] * weights[-1] + labels[i]
                weights[-1] += 1.0
                means[-1] = total / weights[-1]
            else:
                xs.append(x)
                means.append(float(labels[i]))
                weights.append(1.0)
        fitted = _pav(means, weights)
        self._x = xs
        self._y = fitted
        self._fitted = True
        return self

    def predict(self, value: float) -> float:
        """Interpola a probabilidade calibrada para um valor previsto."""
        if not self._fitted:
            raise ValueError("o calibrador precisa ser ajustado com fit()")
        if value <= self._x[0]:
            return self._y[0]
        if value >= self._x[-1]:
            return self._y[-1]
        for i in range(1, len(self._x)):
            if value <= self._x[i]:
                x0, x1 = self._x[i - 1], self._x[i]
                y0, y1 = self._y[i - 1], self._y[i]
                if x1 == x0:
                    return y1
                ratio = (value - x0) / (x1 - x0)
                return y0 + ratio * (y1 - y0)
        return self._y[-1]


class CalibratedTriples:
    """Calibra triplas 1x2 calibrando cada classe e renormalizando."""

    def __init__(self) -> None:
        self._calibrators: list[IsotonicCalibrator] = [IsotonicCalibrator() for _ in range(3)]
        self._fitted = False

    def fit(self, probs: list[ProbTriple], outcomes: list[int]) -> CalibratedTriples:
        """Ajusta um calibrador por classe (one-vs-rest)."""
        for k in range(3):
            preds = [triple[k] for triple in probs]
            labels = [1 if outcome == k else 0 for outcome in outcomes]
            self._calibrators[k].fit(preds, labels)
        self._fitted = True
        return self

    def transform(self, triple: ProbTriple) -> ProbTriple:
        """Calibra uma tripla e renormaliza para somar 1."""
        if not self._fitted:
            raise ValueError("chame fit() antes de transform()")
        calibrated = [self._calibrators[k].predict(triple[k]) for k in range(3)]
        total = sum(calibrated)
        if total <= 0:
            return (1 / 3, 1 / 3, 1 / 3)
        return (calibrated[0] / total, calibrated[1] / total, calibrated[2] / total)
