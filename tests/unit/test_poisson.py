"""Testes do modelo Poisson/Dixon-Coles."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from copamind.data.schemas import Match, MatchStage, MatchStatus
from copamind.models.poisson import PoissonConfig, PoissonModel, poisson_pmf

_BASE = datetime(2025, 1, 1, tzinfo=UTC)
_LINEAGE = {
    "source": "test",
    "collected_at": _BASE,
    "available_at": _BASE,
    "snapshot_id": "s",
}


def _match(mid: str, home: str, away: str, hs: int, as_: int, day: int) -> Match:
    return Match(
        match_id=mid,
        competition="c",
        stage=MatchStage.friendly,
        match_date=_BASE + timedelta(days=day),
        home_team_id=home,
        away_team_id=away,
        home_score=hs,
        away_score=as_,
        status=MatchStatus.finished,
        **_LINEAGE,
    )


def _dataset() -> list[Match]:
    # A é forte, C é fraco.
    return [
        _match("M1", "A", "B", 3, 0, 0),
        _match("M2", "A", "C", 4, 0, 7),
        _match("M3", "B", "C", 2, 1, 14),
        _match("M4", "B", "A", 0, 2, 21),
        _match("M5", "C", "A", 0, 3, 28),
        _match("M6", "C", "B", 1, 1, 35),
    ]


def test_poisson_pmf_sums_to_one() -> None:
    total = sum(poisson_pmf(k, 1.5) for k in range(30))
    assert total == pytest.approx(1.0, abs=1e-6)


def test_pmf_zero_lambda() -> None:
    assert poisson_pmf(0, 0.0) == 1.0
    assert poisson_pmf(1, 0.0) == 0.0


def test_predict_probabilities_sum_to_one() -> None:
    model = PoissonModel()
    model.fit(_dataset())
    pred = model.predict_match("A", "B")
    total = pred.prob_home_win + pred.prob_draw + pred.prob_away_win
    assert total == pytest.approx(1.0, abs=1e-6)


def test_stronger_team_higher_win_prob() -> None:
    model = PoissonModel()
    model.fit(_dataset())
    strong = model.predict_match("A", "C")
    assert strong.prob_home_win > strong.prob_away_win
    assert strong.expected_home_goals > strong.expected_away_goals


def test_dixon_coles_still_normalized() -> None:
    model = PoissonModel(PoissonConfig(use_dixon_coles=True, rho=-0.1))
    model.fit(_dataset())
    pred = model.predict_match("A", "B")
    assert pred.prob_home_win + pred.prob_draw + pred.prob_away_win == pytest.approx(1.0, abs=1e-6)


def test_fit_is_deterministic() -> None:
    m1 = PoissonModel()
    m1.fit(_dataset())
    m2 = PoissonModel()
    m2.fit(list(reversed(_dataset())))
    p1 = m1.predict_match("A", "B")
    p2 = m2.predict_match("A", "B")
    assert p1.expected_home_goals == pytest.approx(p2.expected_home_goals)


def test_predict_requires_fit() -> None:
    with pytest.raises(ValueError, match="fit"):
        PoissonModel().predict_match("A", "B")


def test_fit_requires_finished() -> None:
    with pytest.raises(ValueError, match="finalizada"):
        PoissonModel().fit([])

