"""Serviço de análise: combina Elo e forma recente a partir do repositório."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from copamind.data.repositories import DuckDBRepository
from copamind.features.form import DEFAULT_WINDOWS, TeamFormSummary, compute_form_windows
from copamind.models.elo import EloConfig, EloRatingSystem


class TeamAnalysis(BaseModel):
    """Rating Elo e forma recente de uma seleção."""

    team_id: str
    elo_rating: float
    as_of: datetime | None
    form: TeamFormSummary


def build_elo(repo: DuckDBRepository, *, as_of: datetime | None = None) -> EloRatingSystem:
    """Constrói o sistema Elo processando as partidas finalizadas do repositório."""
    system = EloRatingSystem(EloConfig())
    system.process_matches(repo.list_finished_matches(as_of=as_of))
    return system


def analyze_team(
    repo: DuckDBRepository,
    team_id: str,
    *,
    as_of: datetime | None = None,
    windows: tuple[int, ...] = DEFAULT_WINDOWS,
    decay_lambda: float = 0.0,
) -> TeamAnalysis:
    """Calcula Elo e forma recente de uma seleção (sem vazamento temporal)."""
    matches = repo.list_finished_matches(as_of=as_of)
    elo = EloRatingSystem(EloConfig())
    elo.process_matches(matches)
    form = compute_form_windows(
        matches, team_id, windows=windows, as_of=as_of, decay_lambda=decay_lambda
    )
    return TeamAnalysis(
        team_id=team_id,
        elo_rating=elo.rating(team_id),
        as_of=as_of,
        form=form,
    )
