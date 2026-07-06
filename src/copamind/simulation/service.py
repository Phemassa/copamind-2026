"""Serviço de simulação: monta o modelo e a configuração a partir do repositório."""

from __future__ import annotations

from copamind.data.repositories import DuckDBRepository
from copamind.models.poisson.service import build_poisson
from copamind.simulation.tournament import (
    MonteCarloSimulator,
    SimulationResult,
    TournamentConfig,
)


def build_default_config(
    repo: DuckDBRepository,
    *,
    iterations: int = 10_000,
    seed: int = 2026,
    advance_per_group: int = 2,
) -> TournamentConfig:
    """Cria uma configuração de grupo único com todas as seleções da base.

    Útil para o dataset de amostra. Cenários reais devem fornecer os grupos.
    """
    team_ids = [t.team_id for t in repo.list_teams()]
    return TournamentConfig(
        groups={"A": team_ids},
        advance_per_group=advance_per_group,
        iterations=iterations,
        seed=seed,
    )


def run_simulation(
    repo: DuckDBRepository, config: TournamentConfig | None = None
) -> SimulationResult:
    """Ajusta o modelo Poisson e executa a simulação do torneio."""
    model = build_poisson(repo)
    if config is None:
        config = build_default_config(repo)
    simulator = MonteCarloSimulator(model, config)
    return simulator.simulate()
