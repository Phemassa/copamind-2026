"""Serviço de ingestão: carrega arquivos para o repositório DuckDB.

Registra um snapshot e persiste seleções e partidas com deduplicação.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from copamind.core.logging import get_logger
from copamind.data.connectors.openfootball import read_worldcup_file
from copamind.data.ingestion.loaders import load_matches, load_teams
from copamind.data.repositories import DuckDBRepository
from copamind.data.schemas import PlayerRating, Snapshot

logger = get_logger(__name__)

SAMPLE_DIR = Path("data/samples")
SAMPLE_TEAMS = SAMPLE_DIR / "teams.json"
SAMPLE_MATCHES = SAMPLE_DIR / "matches.json"


@dataclass(frozen=True)
class IngestionResult:
    """Resumo de uma operação de ingestão."""

    teams: int = 0
    matches: int = 0
    snapshot_id: str | None = None


def _ensure_snapshot(repo: DuckDBRepository, snapshot_id: str, description: str) -> None:
    repo.upsert_snapshot(
        Snapshot(
            snapshot_id=snapshot_id,
            created_at=datetime.now(UTC),
            description=description,
        )
    )


def ingest_teams_file(repo: DuckDBRepository, path: str | Path) -> int:
    """Ingere seleções de um arquivo. Retorna a quantidade persistida."""
    repo.create_schema()
    teams = load_teams(path)
    count = repo.upsert_teams(teams)
    logger.info("teams_ingested", count=count, path=str(path))
    return count


def ingest_matches_file(repo: DuckDBRepository, path: str | Path) -> int:
    """Ingere partidas de um arquivo. Retorna a quantidade persistida."""
    repo.create_schema()
    matches = load_matches(path)
    count = repo.upsert_matches(matches)
    logger.info("matches_ingested", count=count, path=str(path))
    return count


def ingest_samples(repo: DuckDBRepository) -> IngestionResult:
    """Ingere o dataset sintético de amostra.

    Raises:
        FileNotFoundError: se os arquivos de amostra não existirem.
    """
    if not SAMPLE_TEAMS.exists() or not SAMPLE_MATCHES.exists():
        raise FileNotFoundError("Amostra ausente. Gere com: python scripts/download_sample_data.py")
    repo.create_schema()
    snapshot_id = "sample-2026-07-06"
    _ensure_snapshot(repo, snapshot_id, "Dataset sintético de amostra")
    teams = ingest_teams_file(repo, SAMPLE_TEAMS)
    matches = ingest_matches_file(repo, SAMPLE_MATCHES)
    return IngestionResult(teams=teams, matches=matches, snapshot_id=snapshot_id)


def ingest_worldcup(
    repo: DuckDBRepository, path: str | Path, *, snapshot_id: str = "worldcup-openfootball"
) -> IngestionResult:
    """Ingere um `worldcup.json` do OpenFootball (dados reais/estáticos)."""
    repo.create_schema()
    _ensure_snapshot(repo, snapshot_id, "OpenFootball worldcup.json")
    teams, matches = read_worldcup_file(path, snapshot_id=snapshot_id)
    n_teams = repo.upsert_teams(teams)
    n_matches = repo.upsert_matches(matches)
    logger.info("worldcup_ingested", teams=n_teams, matches=n_matches, path=str(path))
    return IngestionResult(teams=n_teams, matches=n_matches, snapshot_id=snapshot_id)


def ingest_players(repo: DuckDBRepository, path: str | Path) -> int:
    """Ingere ratings de jogadores de um arquivo JSON.

    O arquivo deve conter uma lista de objetos compatíveis com PlayerRating.
    """
    import json

    repo.create_schema()
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    players = [PlayerRating.model_validate(p) for p in raw]
    count = repo.upsert_players(players)
    logger.info("players_ingested", count=count, path=str(path))
    return count
