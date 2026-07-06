"""Rotas de previsão de partidas (MASTER_PLAN §20)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from copamind.api.dependencies import get_repository
from copamind.data.repositories import DuckDBRepository
from copamind.models.ensemble.service import EnsemblePrediction, ensemble_match
from copamind.models.poisson import MatchPrediction
from copamind.models.poisson.service import predict_match

router = APIRouter(tags=["predictions"], prefix="/predictions")

RepoDep = Annotated[DuckDBRepository, Depends(get_repository)]


class MatchPredictionRequest(BaseModel):
    """Corpo da requisição de previsão de partida."""

    home_team_id: str
    away_team_id: str
    neutral_venue: bool = False


@router.post("/match", response_model=MatchPrediction)
def predict(request: MatchPredictionRequest, repo: RepoDep) -> MatchPrediction:
    """Prediz uma partida (Poisson/Dixon-Coles) e persiste o resultado."""
    if request.home_team_id == request.away_team_id:
        raise HTTPException(status_code=422, detail="times devem ser diferentes")
    for team_id in (request.home_team_id, request.away_team_id):
        if repo.get_team(team_id) is None:
            raise HTTPException(status_code=404, detail=f"team not found: {team_id}")
    return predict_match(
        repo,
        request.home_team_id,
        request.away_team_id,
        neutral_venue=request.neutral_venue,
    )


@router.post("/ensemble", response_model=EnsemblePrediction)
def predict_ensemble(request: MatchPredictionRequest, repo: RepoDep) -> EnsemblePrediction:
    """Prediz uma partida combinando Elo e Poisson (ensemble)."""
    if request.home_team_id == request.away_team_id:
        raise HTTPException(status_code=422, detail="times devem ser diferentes")
    for team_id in (request.home_team_id, request.away_team_id):
        if repo.get_team(team_id) is None:
            raise HTTPException(status_code=404, detail=f"team not found: {team_id}")
    return ensemble_match(
        repo,
        request.home_team_id,
        request.away_team_id,
        neutral_venue=request.neutral_venue,
    )
