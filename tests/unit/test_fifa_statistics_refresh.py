"""Testes do orquestrador de atualizacao FIFA."""

from __future__ import annotations

from pathlib import Path

from copamind.data.fifa_fixtures import FIFAFixtureConnector, FIFARefreshResult
from copamind.data.fifa_statistics_refresh import (
    RefreshSummary,
    refresh_all_fifa_data,
    refresh_player_statistics,
)
from copamind.data.repositories import DuckDBRepository


def test_refresh_all_fifa_data_combines_steps(monkeypatch) -> None:
    def fake_fixture_refresh(self, repo, *, force_network=False):
        return FIFARefreshResult(matches=12, source="network", cache_path=Path("cache.json"))

    monkeypatch.setattr(FIFAFixtureConnector, "refresh", fake_fixture_refresh)
    monkeypatch.setattr(
        "copamind.data.fifa_statistics_refresh.refresh_team_statistics",
        lambda *, force_network=True: RefreshSummary(
            name="Equipes", source="fake", rows=48, files=9
        ),
    )
    monkeypatch.setattr(
        "copamind.data.fifa_statistics_refresh.refresh_player_statistics",
        lambda *, force_network=True: RefreshSummary(
            name="Jogadores", source="fake", rows=640, files=10
        ),
    )

    with DuckDBRepository(":memory:") as repo:
        summary = refresh_all_fifa_data(repo)

    assert summary.fixtures.rows == 12
    assert summary.team_statistics.files == 9
    assert summary.player_statistics.rows == 640
    assert summary.warnings == []


def test_refresh_player_statistics_keeps_local_data_on_failure(monkeypatch) -> None:
    def broken_refresh():
        raise RuntimeError("rate limited")

    monkeypatch.setattr(
        "scripts.fetch_fifa_player_statistics.refresh_player_statistics",
        broken_refresh,
    )

    summary = refresh_player_statistics()

    assert summary.source == "cache/local"
    assert summary.warning is not None
    assert "mantendo CSVs locais" in summary.warning
