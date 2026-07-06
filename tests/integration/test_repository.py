"""Testes de integração do repositório DuckDB."""

from __future__ import annotations

from datetime import datetime

from copamind.data.repositories import DuckDBRepository
from copamind.data.schemas import MatchStatus


def test_seeded_counts(seeded_repo: DuckDBRepository) -> None:
    assert seeded_repo.count("teams") == 48
    assert seeded_repo.count("matches") == 92
    assert seeded_repo.count("snapshots") == 1


def test_create_schema_idempotent(seeded_repo: DuckDBRepository) -> None:
    # Chamar novamente não deve falhar nem duplicar dados.
    seeded_repo.create_schema()
    assert seeded_repo.count("teams") == 48


def test_list_and_get_team(seeded_repo: DuckDBRepository) -> None:
    teams = seeded_repo.list_teams()
    assert len(teams) == 48
    team = seeded_repo.get_team("T-BRA")
    assert team is not None
    assert team.fifa_code == "BRA"
    assert seeded_repo.get_team("inexistente") is None


def test_last_matches_ordering(seeded_repo: DuckDBRepository) -> None:
    matches = seeded_repo.get_last_matches("T-BRA", limit=3)
    assert len(matches) == 3
    dates = [m.match_date for m in matches]
    assert dates == sorted(dates, reverse=True)
    assert all(m.status is MatchStatus.finished for m in matches)


def test_last_matches_as_of_prevents_leakage(seeded_repo: DuckDBRepository) -> None:
    # Antes de qualquer partida disponível, não deve retornar nada.
    early = datetime(2024, 1, 1)
    assert seeded_repo.get_last_matches("T-BRA", as_of=early) == []


def test_upsert_is_idempotent(seeded_repo: DuckDBRepository) -> None:
    before = seeded_repo.count("teams")
    teams = seeded_repo.list_teams()
    seeded_repo.upsert_teams(teams)  # reprocessar não duplica (PK)
    assert seeded_repo.count("teams") == before


