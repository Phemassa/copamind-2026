"""Testes de pontuação do bolão."""

from __future__ import annotations

import pytest

from copamind.pool.scoring import bolao_points, brier_score, outcome


def test_outcome() -> None:
    assert outcome(2, 0) == "home"
    assert outcome(1, 1) == "draw"
    assert outcome(0, 3) == "away"


def test_exact_score_points() -> None:
    assert bolao_points(2, 1, 2, 1) == 5


def test_correct_result_points() -> None:
    # Previu vitória do mandante (2x1); resultado vitória do mandante (3x0).
    assert bolao_points(2, 1, 3, 0) == 3


def test_wrong_points() -> None:
    assert bolao_points(2, 1, 0, 1) == 0


def test_brier_perfect() -> None:
    assert brier_score(1.0, 0.0, 0.0, "home") == pytest.approx(0.0)


def test_brier_worst() -> None:
    assert brier_score(0.0, 0.0, 1.0, "home") == pytest.approx(2.0)


def test_brier_bounds() -> None:
    value = brier_score(0.5, 0.3, 0.2, "draw")
    assert 0.0 <= value <= 2.0

