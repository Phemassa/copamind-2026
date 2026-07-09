"""Orquestracao de sync dos dados FIFA usados pelo portal."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from copamind.data.fifa_fixtures import FIFAFixtureConnector
from copamind.data.fifa_match_extras import clear_match_extras_cache
from copamind.data.fifa_stats import clear_fifa_stats_cache
from copamind.data.repositories import DuckDBRepository


@dataclass(frozen=True)
class RefreshSummary:
    """Resumo de uma etapa de atualizacao."""

    name: str
    source: str
    rows: int = 0
    files: int = 0
    warning: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FifaSyncSummary:
    """Resumo consolidado da atualizacao FIFA."""

    created_at: datetime
    fixtures: RefreshSummary
    team_statistics: RefreshSummary
    player_statistics: RefreshSummary

    @property
    def warnings(self) -> list[str]:
        return [
            item.warning
            for item in (self.fixtures, self.team_statistics, self.player_statistics)
            if item.warning
        ]


def refresh_team_statistics(*, force_network: bool = True) -> RefreshSummary:
    """Atualiza os CSVs de estatisticas de selecoes."""
    del force_network
    try:
        from scripts.fetch_fifa_team_statistics import refresh_team_statistics as refresh

        summary = refresh()
        clear_fifa_stats_cache()
        return RefreshSummary(
            name="Estatisticas de equipes",
            source="fifa-gameday",
            rows=int(summary.get("rows") or 0),
            files=int(summary.get("files") or 0),
            details=summary,
        )
    except Exception as exc:  # pragma: no cover - protegido pela UI e testes via monkeypatch.
        return RefreshSummary(
            name="Estatisticas de equipes",
            source="cache/local",
            warning=f"Falha ao atualizar equipes; mantendo CSVs locais. {exc}",
        )


def refresh_player_statistics(*, force_network: bool = True) -> RefreshSummary:
    """Atualiza os CSVs de estatisticas e imagens de jogadores."""
    del force_network
    try:
        from scripts.fetch_fifa_player_statistics import refresh_player_statistics as refresh

        summary = refresh()
        clear_fifa_stats_cache()
        return RefreshSummary(
            name="Estatisticas de jogadores",
            source="fifa-gameday",
            rows=int(summary.get("rows") or 0),
            files=int(summary.get("files") or 0),
            details=summary,
        )
    except Exception as exc:  # pragma: no cover - protegido pela UI e testes via monkeypatch.
        return RefreshSummary(
            name="Estatisticas de jogadores",
            source="cache/local",
            warning=f"Falha ao atualizar jogadores; mantendo CSVs locais. {exc}",
        )


def refresh_all_fifa_data(
    repo: DuckDBRepository, *, force_network: bool = True
) -> FifaSyncSummary:
    """Atualiza jogos, estatisticas de equipes e jogadores em uma chamada."""
    fixture_result = FIFAFixtureConnector().refresh(repo, force_network=force_network)
    clear_match_extras_cache()
    fixtures = RefreshSummary(
        name="Jogos",
        source=fixture_result.source,
        rows=fixture_result.matches,
        files=1,
        warning=fixture_result.warning,
    )
    team_stats = refresh_team_statistics(force_network=force_network)
    player_stats = refresh_player_statistics(force_network=force_network)
    clear_fifa_stats_cache()
    return FifaSyncSummary(
        created_at=datetime.now(UTC),
        fixtures=fixtures,
        team_statistics=team_stats,
        player_statistics=player_stats,
    )
