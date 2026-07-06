"""Rotas de dados: seleções e partidas (MASTER_PLAN §20)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from copamind.api.dependencies import get_repository
from copamind.data.repositories import DuckDBRepository
from copamind.data.schemas import Match, Team

router = APIRouter(tags=["data"])

RepoDep = Annotated[DuckDBRepository, Depends(get_repository)]


@router.get("/teams", response_model=list[Team])
def list_teams(repo: RepoDep) -> list[Team]:
    """Lista todas as seleções."""
    return repo.list_teams()


@router.get("/teams/{team_id}", response_model=Team)
def get_team(team_id: str, repo: RepoDep) -> Team:
    """Retorna uma seleção pelo id."""
    team = repo.get_team(team_id)
    if team is None:
        raise HTTPException(status_code=404, detail="team not found")
    return team


@router.get("/teams/{team_id}/last-matches", response_model=list[Match])
def last_matches(
    team_id: str,
    repo: RepoDep,
    limit: Annotated[int, Query(ge=1, le=50)] = 5,
) -> list[Match]:
    """Retorna as últimas partidas finalizadas de uma seleção."""
    return repo.get_last_matches(team_id, limit=limit)


@router.get("/matches", response_model=list[Match])
def list_matches(
    repo: RepoDep,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[Match]:
    """Lista partidas ordenadas por data (mais recentes primeiro)."""
    return repo.list_matches(limit=limit)
