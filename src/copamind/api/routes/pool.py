"""Rotas do Bolão de IAs Locais (E11)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from copamind.api.dependencies import get_repository
from copamind.data.repositories import DuckDBRepository
from copamind.pool.service import (
    BacktestSummary,
    PredictorStanding,
    leaderboard,
    run_backtest,
)

router = APIRouter(tags=["pool"], prefix="/pool")

RepoDep = Annotated[DuckDBRepository, Depends(get_repository)]


@router.post("/backtest", response_model=BacktestSummary)
def backtest(repo: RepoDep) -> BacktestSummary:
    """Roda o bolão sobre o histórico e retorna a classificação dos preditores."""
    return run_backtest(repo)


@router.get("/leaderboard", response_model=list[PredictorStanding])
def get_leaderboard(repo: RepoDep) -> list[PredictorStanding]:
    """Retorna a classificação atual do bolão."""
    return leaderboard(repo)
