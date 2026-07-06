"""Ingestão de dados: leitura, validação (Pydantic) e deduplicação.

Regras (MASTER_PLAN §1.7, §18): todo registro carrega linhagem; duplicatas
são removidas antes da persistência. Dados inválidos são rejeitados com erro.
"""

from copamind.data.ingestion.loaders import (
    IngestionError,
    dedupe_matches,
    dedupe_teams,
    load_matches,
    load_teams,
)

__all__ = [
    "IngestionError",
    "dedupe_matches",
    "dedupe_teams",
    "load_matches",
    "load_teams",
]
