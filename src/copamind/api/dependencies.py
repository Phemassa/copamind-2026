"""Dependências compartilhadas da API."""

from __future__ import annotations

from collections.abc import Iterator

from copamind.core.config import get_settings
from copamind.data.repositories import DuckDBRepository


def get_repository() -> Iterator[DuckDBRepository]:
    """Fornece um repositório DuckDB por requisição (fecha ao final).

    Sobrescreva via ``app.dependency_overrides`` em testes.
    """
    settings = get_settings()
    repo = DuckDBRepository(settings.duckdb_path)
    repo.create_schema()
    try:
        yield repo
    finally:
        repo.close()
