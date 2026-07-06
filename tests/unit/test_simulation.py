"""Testes do simulador Monte Carlo do torneio."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from copamind.data.schemas import Match, MatchStage, MatchStatus
from copamind.models.poisson import PoissonModel
from copamind.simulation.tournament import MonteCarloSimulator, TournamentConfig

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


def _model() -> PoissonModel:
    # A domina; D é fraco.
    matches = [
        _match("M1", "A", "B", 3, 0, 0),
        _match("M2", "A", "C", 2, 0, 7),
        _match("M3", "A", "D", 4, 0, 14),
        _match("M4", "B", "C", 1, 1, 21),
        _match("M5", "B", "D", 2, 0, 28),
        _match("M6", "C", "D", 2, 1, 35),
    ]
    model = PoissonModel()
    model.fit(matches)
    return model


def _config(iterations: int = 2000) -> TournamentConfig:
    return TournamentConfig(
        groups={"A": ["A", "B", "C", "D"]},
        advance_per_group=2,
        iterations=iterations,
        seed=2026,
    )


def test_config_rejects_non_power_of_two() -> None:
    with pytest.raises(ValidationError):
        TournamentConfig(groups={"A": ["A", "B", "C"]}, advance_per_group=1)


def test_config_rejects_small_group() -> None:
    with pytest.raises(ValidationError):
        TournamentConfig(groups={"A": ["A"]}, advance_per_group=2)


def test_champion_probabilities_sum_to_one() -> None:
    result = MonteCarloSimulator(_model(), _config()).simulate()
    total = sum(t.champion_probability for t in result.teams)
    assert total == pytest.approx(1.0, abs=1e-9)


def test_qualified_probabilities_sum_to_qualifiers() -> None:
    config = _config()
    result = MonteCarloSimulator(_model(), config).simulate()
    total = sum(t.qualified_probability for t in result.teams)
    assert total == pytest.approx(config.qualifiers_count, abs=1e-9)


def test_reproducible_with_seed() -> None:
    r1 = MonteCarloSimulator(_model(), _config()).simulate()
    r2 = MonteCarloSimulator(_model(), _config()).simulate()
    assert [t.champion_probability for t in r1.teams] == [t.champion_probability for t in r2.teams]


def test_stronger_team_more_likely_champion() -> None:
    result = MonteCarloSimulator(_model(), _config()).simulate()
    champ = {t.team_id: t.champion_probability for t in result.teams}
    assert champ["A"] > champ["D"]


def test_stage_probabilities_present() -> None:
    # 4 classificados (todos avançam) => mata-mata com semifinal e final.
    config = TournamentConfig(
        groups={"A": ["A", "B", "C", "D"]},
        advance_per_group=4,
        iterations=2000,
        seed=2026,
    )
    result = MonteCarloSimulator(_model(), config).simulate()
    for team in result.teams:
        assert set(team.stage_probabilities) == {"semifinal", "final"}
        # Reachar a final implica reachar a semifinal.
        assert team.stage_probabilities["semifinal"] >= team.stage_probabilities["final"]


