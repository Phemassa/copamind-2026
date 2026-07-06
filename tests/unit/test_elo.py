"""Testes do sistema de rating Elo."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from copamind.data.schemas import Match, MatchStage, MatchStatus
from copamind.models.elo import (
    EloConfig,
    EloRatingSystem,
    expected_score,
    goal_difference_multiplier,
)

_BASE = datetime(2025, 1, 1, tzinfo=UTC)
_LINEAGE = {
    "source": "test",
    "collected_at": _BASE,
    "available_at": _BASE,
    "snapshot_id": "s",
}


def _match(mid: str, home: str, away: str, hs: int, as_: int, day: int = 0) -> Match:
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


def test_expected_score_symmetry() -> None:
    assert expected_score(1500, 1500) == pytest.approx(0.5)
    assert expected_score(1700, 1500) > 0.5
    assert expected_score(1300, 1500) < 0.5


def test_goal_difference_multiplier() -> None:
    assert goal_difference_multiplier(0) == 1.0
    assert goal_difference_multiplier(1) == 1.0
    assert goal_difference_multiplier(2) == 1.5
    assert goal_difference_multiplier(3) == pytest.approx(14 / 8)


def test_zero_sum_after_match() -> None:
    system = EloRatingSystem(EloConfig())
    system.process_match(_match("M1", "A", "B", 2, 0))
    total = system.rating("A") + system.rating("B")
    assert total == pytest.approx(2 * EloConfig().base_rating)


def test_home_win_increases_rating() -> None:
    system = EloRatingSystem(EloConfig())
    system.process_match(_match("M1", "A", "B", 1, 0))
    assert system.rating("A") > 1500
    assert system.rating("B") < 1500


def test_reproducible_and_order_independent() -> None:
    matches = [
        _match("M1", "A", "B", 2, 0, day=0),
        _match("M2", "B", "C", 1, 1, day=1),
        _match("M3", "A", "C", 0, 3, day=2),
    ]
    s1 = EloRatingSystem(EloConfig())
    s1.process_matches(matches)
    s2 = EloRatingSystem(EloConfig())
    s2.process_matches(list(reversed(matches)))
    assert s1.ratings() == s2.ratings()


def test_win_probability_home_advantage() -> None:
    system = EloRatingSystem(EloConfig())
    p_home = system.win_probability("A", "B")
    p_neutral = system.win_probability("A", "B", neutral_venue=True)
    assert p_home > p_neutral == pytest.approx(0.5)


def test_process_requires_finished() -> None:
    scheduled = Match(
        match_id="M1",
        competition="c",
        stage=MatchStage.friendly,
        match_date=_BASE,
        home_team_id="A",
        away_team_id="B",
        status=MatchStatus.scheduled,
        **_LINEAGE,
    )
    with pytest.raises(ValueError, match="finalizadas"):
        EloRatingSystem(EloConfig()).process_match(scheduled)


