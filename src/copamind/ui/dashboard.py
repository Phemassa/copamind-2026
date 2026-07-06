"""Helpers de dados do dashboard (testáveis, sem dependência de Streamlit).

Montam estruturas simples a partir do repositório e dos serviços preditivos,
mantendo o app Streamlit fino e coberto por testes nesta camada.
"""

from __future__ import annotations

from typing import Any

from copamind.data.repositories import DuckDBRepository
from copamind.features.service import analyze_team
from copamind.models.poisson.service import predict_match
from copamind.pool.service import run_backtest
from copamind.simulation.service import build_default_config, run_simulation


def database_status(repo: DuckDBRepository) -> dict[str, Any]:
    """Resumo do estado da base para a página inicial."""
    return {
        "teams": repo.count("teams"),
        "matches": repo.count("matches"),
        "predictions": repo.count("predictions"),
        "snapshot": repo.latest_snapshot_id(),
    }


def championship_table(
    repo: DuckDBRepository, *, iterations: int = 5000, seed: int = 2026
) -> list[dict[str, Any]]:
    """Tabela de chances de classificação e título por seleção."""
    config = build_default_config(repo, iterations=iterations, seed=seed)
    result = run_simulation(repo, config)
    return [
        {
            "team_id": team.team_id,
            "qualify": team.qualified_probability,
            "title": team.champion_probability,
        }
        for team in result.teams
    ]


def team_analysis_view(repo: DuckDBRepository, team_id: str) -> dict[str, Any]:
    """Rating Elo, forma por janelas e últimas partidas de uma seleção."""
    analysis = analyze_team(repo, team_id)
    last = repo.get_last_matches(team_id, limit=5)
    return {
        "team_id": team_id,
        "elo_rating": analysis.elo_rating,
        "windows": [w.model_dump() for w in analysis.form.windows],
        "last_matches": [
            {
                "match_id": m.match_id,
                "home_team_id": m.home_team_id,
                "away_team_id": m.away_team_id,
                "home_score": m.home_score,
                "away_score": m.away_score,
                "match_date": m.match_date,
            }
            for m in last
        ],
    }


def match_prediction_view(
    repo: DuckDBRepository, home_id: str, away_id: str, *, neutral_venue: bool = False
) -> dict[str, Any]:
    """Previsão 1x2 e gols esperados para um confronto (sem persistir)."""
    prediction = predict_match(repo, home_id, away_id, neutral_venue=neutral_venue, persist=False)
    return prediction.model_dump()


def pool_leaderboard_view(repo: DuckDBRepository) -> list[dict[str, Any]]:
    """Roda o bolão sobre o histórico e retorna a classificação dos preditores."""
    summary = run_backtest(repo)
    return [standing.model_dump() for standing in summary.standings]
