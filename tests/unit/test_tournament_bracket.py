"""Testes do bracket dinamico do portal."""

from __future__ import annotations

from datetime import UTC, datetime

from copamind.data.schemas import Match, MatchStage, MatchStatus
from copamind.ui.tournament import build_bracket_html


def _match(match_id: str, stage: MatchStage, status: MatchStatus = MatchStatus.scheduled) -> Match:
    return Match(
        match_id=match_id,
        competition="World Cup",
        stage=stage,
        match_date=datetime(2026, 7, 1, 20, tzinfo=UTC),
        home_team_id="T-BRA",
        away_team_id="T-FRA",
        neutral_venue=True,
        home_score=2 if status is MatchStatus.finished else None,
        away_score=1 if status is MatchStatus.finished else None,
        status=status,
        source="test",
        collected_at=datetime.now(UTC),
        available_at=datetime.now(UTC),
        snapshot_id="test",
    )


def test_bracket_uses_matches_and_consensus() -> None:
    html = build_bracket_html(
        [_match("m1", MatchStage.round_of_16, MatchStatus.finished)],
        consensus_by_match={"m1": "2-1 61% | modelo"},
    )

    assert "Oitavas" in html
    assert "Brasil" in html
    assert "Fran" in html
    assert "2-1 61% | modelo" in html
    assert "finalizado" in html


def test_bracket_renders_undefined_slots() -> None:
    html = build_bracket_html([])

    assert "Chave mata-mata CopaMind" in html
    assert "A definir" in html
