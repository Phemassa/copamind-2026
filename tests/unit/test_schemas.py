"""Testes dos schemas de domínio."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from copamind.data.schemas import Confederation, Match, MatchStage, MatchStatus, Team

_NOW = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
_LINEAGE = {
    "source": "test",
    "collected_at": _NOW,
    "available_at": _NOW,
    "snapshot_id": "snap-1",
}


def test_valid_team() -> None:
    team = Team(
        team_id="T-1",
        name="Nortlândia",
        fifa_code="NTL",
        country="Nortlândia",
        confederation=Confederation.uefa,
        **_LINEAGE,
    )
    assert team.active is True
    assert team.confederation is Confederation.uefa


def test_team_requires_lineage() -> None:
    with pytest.raises(ValidationError):
        Team(
            team_id="T-1",
            name="X",
            fifa_code="XXX",
            country="X",
            confederation=Confederation.afc,
        )  # type: ignore[call-arg]


def test_match_rejects_same_teams() -> None:
    with pytest.raises(ValidationError):
        Match(
            match_id="M-1",
            competition="c",
            stage=MatchStage.group,
            match_date=_NOW,
            home_team_id="T-1",
            away_team_id="T-1",
            **_LINEAGE,
        )


def test_finished_match_requires_scores() -> None:
    with pytest.raises(ValidationError):
        Match(
            match_id="M-2",
            competition="c",
            stage=MatchStage.group,
            match_date=_NOW,
            home_team_id="T-1",
            away_team_id="T-2",
            status=MatchStatus.finished,
            **_LINEAGE,
        )


def test_negative_score_rejected() -> None:
    with pytest.raises(ValidationError):
        Match(
            match_id="M-3",
            competition="c",
            stage=MatchStage.group,
            match_date=_NOW,
            home_team_id="T-1",
            away_team_id="T-2",
            home_score=-1,
            away_score=0,
            status=MatchStatus.finished,
            **_LINEAGE,
        )


