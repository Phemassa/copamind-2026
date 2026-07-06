"""Rotas de simulação do torneio (MASTER_PLAN §20)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, ValidationError

from copamind.api.dependencies import get_repository
from copamind.data.repositories import DuckDBRepository
from copamind.simulation.service import build_default_config, run_simulation
from copamind.simulation.tournament import SimulationResult, TournamentConfig

router = APIRouter(tags=["simulations"], prefix="/simulations")

RepoDep = Annotated[DuckDBRepository, Depends(get_repository)]


class SimulationRequest(BaseModel):
    """Corpo da requisição de simulação."""

    iterations: int = Field(default=10_000, ge=1, le=200_000)
    seed: int = 2026
    advance_per_group: int = Field(default=2, ge=1)
    groups: dict[str, list[str]] | None = None


@router.post("", response_model=SimulationResult)
def simulate(request: SimulationRequest, repo: RepoDep) -> SimulationResult:
    """Executa a simulação Monte Carlo e retorna as probabilidades por seleção."""
    if request.groups is None:
        config = build_default_config(
            repo,
            iterations=request.iterations,
            seed=request.seed,
            advance_per_group=request.advance_per_group,
        )
    else:
        try:
            config = TournamentConfig(
                groups=request.groups,
                advance_per_group=request.advance_per_group,
                iterations=request.iterations,
                seed=request.seed,
            )
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
    return run_simulation(repo, config)
