"""Ferramentas do `copamind-mcp` (MASTER_PLAN §13.3).

Funções puras e testáveis que envolvem repositório e serviços, retornando
estruturas serializáveis. Ferramentas read-only e de escrita são separadas
(princípio do menor privilégio, §13.4).
"""

from __future__ import annotations

from typing import Any

from copamind.data.repositories import DuckDBRepository
from copamind.data.schemas import Match, Team
from copamind.features.service import analyze_team
from copamind.models.calibration.report import calibration_report
from copamind.models.ensemble.service import ensemble_match
from copamind.models.poisson.service import predict_match as _predict_match
from copamind.pool.service import leaderboard
from copamind.rag.service import RagService
from copamind.reports.service import create_user_report as _create_user_report
from copamind.reports.service import delete_user_report as _delete_user_report
from copamind.reports.service import verify_user_report as _verify_user_report
from copamind.simulation.service import run_simulation


def _team_dict(team: Team) -> dict[str, Any]:
    return {
        "team_id": team.team_id,
        "name": team.name,
        "fifa_code": team.fifa_code,
        "confederation": str(team.confederation),
        "elo_rating": team.elo_rating,
    }


def _match_dict(match: Match) -> dict[str, Any]:
    return {
        "match_id": match.match_id,
        "match_date": match.match_date.isoformat(),
        "home_team_id": match.home_team_id,
        "away_team_id": match.away_team_id,
        "home_score": match.home_score,
        "away_score": match.away_score,
        "status": str(match.status),
    }


# -- Read-only -----------------------------------------------------------------
def list_teams(repo: DuckDBRepository) -> list[dict[str, Any]]:
    """Lista as seleções cadastradas."""
    return [_team_dict(t) for t in repo.list_teams()]


def get_team(repo: DuckDBRepository, team_id: str) -> dict[str, Any] | None:
    """Retorna uma seleção pelo id."""
    team = repo.get_team(team_id)
    return _team_dict(team) if team else None


def get_last_matches(repo: DuckDBRepository, team_id: str, limit: int = 5) -> list[dict[str, Any]]:
    """Últimas partidas finalizadas de uma seleção."""
    return [_match_dict(m) for m in repo.get_last_matches(team_id, limit=limit)]


def get_head_to_head(
    repo: DuckDBRepository, team_a: str, team_b: str, limit: int = 10
) -> list[dict[str, Any]]:
    """Confrontos diretos entre duas seleções."""
    pair = {team_a, team_b}
    matches = [m for m in repo.list_finished_matches() if {m.home_team_id, m.away_team_id} == pair]
    matches.sort(key=lambda m: m.match_date, reverse=True)
    return [_match_dict(m) for m in matches[:limit]]


def get_team_form(repo: DuckDBRepository, team_id: str) -> dict[str, Any]:
    """Rating Elo e forma recente de uma seleção."""
    return analyze_team(repo, team_id).model_dump()


def predict_match(
    repo: DuckDBRepository, home_team_id: str, away_team_id: str, neutral_venue: bool = False
) -> dict[str, Any]:
    """Previsão 1x2 (Poisson/Dixon-Coles) sem persistir."""
    prediction = _predict_match(
        repo, home_team_id, away_team_id, neutral_venue=neutral_venue, persist=False
    )
    return prediction.model_dump()


def ensemble_predict(
    repo: DuckDBRepository, home_team_id: str, away_team_id: str, neutral_venue: bool = False
) -> dict[str, Any]:
    """Previsão 1x2 combinando Elo e Poisson (ensemble)."""
    return ensemble_match(
        repo, home_team_id, away_team_id, neutral_venue=neutral_venue
    ).model_dump()


def run_tournament_simulation(
    repo: DuckDBRepository, iterations: int = 10_000, seed: int = 2026
) -> list[dict[str, Any]]:
    """Simula o torneio e retorna as probabilidades por seleção."""
    from copamind.simulation.service import build_default_config

    config = build_default_config(repo, iterations=iterations, seed=seed)
    result = run_simulation(repo, config)
    return [
        {
            "team_id": t.team_id,
            "qualified_probability": t.qualified_probability,
            "champion_probability": t.champion_probability,
        }
        for t in result.teams
    ]


def get_data_freshness(repo: DuckDBRepository) -> dict[str, Any]:
    """Estado e frescor da base de dados."""
    return {
        "snapshot_id": repo.latest_snapshot_id(),
        "teams": repo.count("teams"),
        "matches": repo.count("matches"),
        "predictions": repo.count("predictions"),
        "user_reports": repo.count("user_reports"),
    }


def get_calibration(repo: DuckDBRepository) -> list[dict[str, Any]]:
    """Relatório de calibração por preditor (requer bolão executado)."""
    return [report.model_dump() for report in calibration_report(repo)]


def get_pool_leaderboard(repo: DuckDBRepository) -> list[dict[str, Any]]:
    """Classificação do Bolão de IAs."""
    return [standing.model_dump() for standing in leaderboard(repo)]


def search_knowledge(repo: DuckDBRepository, query: str, top_k: int = 5) -> list[dict[str, Any]]:
    """Busca RAG sobre os relatos do usuário (indexa sob demanda)."""
    service = RagService()
    service.index_user_reports(repo)
    results = service.search(query, top_k=top_k)
    return [
        {
            "chunk_id": r.chunk.chunk_id,
            "text": r.chunk.text,
            "score": r.score,
            "source_type": r.chunk.source_type,
            "verified": r.chunk.verified,
        }
        for r in results
    ]


# -- Escrita (exigem confirmação da aplicação) ---------------------------------
def add_user_report(repo: DuckDBRepository, text: str) -> dict[str, Any]:
    """Registra um relato do usuário (source_type=user_input, não verificado)."""
    return _create_user_report(repo, text).model_dump()


def verify_user_report(repo: DuckDBRepository, report_id: str) -> dict[str, Any] | None:
    """Marca um relato como verificado."""
    report = _verify_user_report(repo, report_id)
    return report.model_dump() if report else None


def delete_user_report(repo: DuckDBRepository, report_id: str) -> bool:
    """Exclui um relato (tombstone; histórico preservado)."""
    return _delete_user_report(repo, report_id)


READ_ONLY_TOOLS = (
    list_teams,
    get_team,
    get_last_matches,
    get_head_to_head,
    get_team_form,
    predict_match,
    ensemble_predict,
    run_tournament_simulation,
    get_data_freshness,
    get_calibration,
    get_pool_leaderboard,
    search_knowledge,
)

WRITE_TOOLS = (add_user_report, verify_user_report, delete_user_report)
