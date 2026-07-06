"""Forma recente por janelas (MASTER_PLAN §17.1, §17.2).

Calcula pontos, gols e aproveitamento nas últimas N partidas de uma seleção,
com opção de decaimento temporal ``weight = exp(-lambda * days_since_match)``.
Anti-leakage: o chamador deve fornecer apenas partidas disponíveis até a data
de referência (``available_at <= as_of``).
"""

from __future__ import annotations

import math
from datetime import datetime

from pydantic import BaseModel, Field

from copamind.data.schemas import Match

DEFAULT_WINDOWS = (5, 10, 15)


class FormWindow(BaseModel):
    """Resumo de forma para uma janela de N partidas."""

    window: int = Field(gt=0)
    matches: int = Field(ge=0)
    wins: int = Field(ge=0)
    draws: int = Field(ge=0)
    losses: int = Field(ge=0)
    points: int = Field(ge=0)
    goals_for: int = Field(ge=0)
    goals_against: int = Field(ge=0)
    goal_difference: int
    win_rate: float = Field(ge=0, le=1)
    points_per_game: float = Field(ge=0, le=3)
    points_per_game_weighted: float = Field(ge=0, le=3)


class TeamFormSummary(BaseModel):
    """Forma de uma seleção em múltiplas janelas."""

    team_id: str
    as_of: datetime | None = None
    windows: list[FormWindow]


def _perspective(match: Match, team_id: str) -> tuple[int, int]:
    """Retorna (gols_pro, gols_contra) do ponto de vista da seleção."""
    assert match.home_score is not None and match.away_score is not None
    if match.home_team_id == team_id:
        return match.home_score, match.away_score
    return match.away_score, match.home_score


def compute_form(
    matches: list[Match],
    team_id: str,
    *,
    window: int,
    as_of: datetime | None = None,
    decay_lambda: float = 0.0,
) -> FormWindow:
    """Calcula a forma de ``team_id`` nas últimas ``window`` partidas.

    Args:
        matches: partidas candidatas (serão filtradas pela seleção e finalização).
        team_id: seleção alvo.
        window: número de partidas consideradas (as mais recentes).
        as_of: data de referência para o decaimento; se ausente usa a partida
            mais recente considerada.
        decay_lambda: taxa de decaimento temporal (0 desativa a ponderação).
    """
    relevant = [
        m
        for m in matches
        if m.status.value == "finished"
        and (m.home_team_id == team_id or m.away_team_id == team_id)
        and m.home_score is not None
        and m.away_score is not None
    ]
    relevant.sort(key=lambda m: m.match_date, reverse=True)
    considered = relevant[:window]

    wins = draws = losses = goals_for = goals_against = points = 0
    weighted_points = 0.0
    weight_sum = 0.0
    reference = as_of or (considered[0].match_date if considered else None)

    for match in considered:
        gf, ga = _perspective(match, team_id)
        goals_for += gf
        goals_against += ga
        if gf > ga:
            wins += 1
            result_points = 3
        elif gf == ga:
            draws += 1
            result_points = 1
        else:
            losses += 1
            result_points = 0
        points += result_points

        if decay_lambda > 0.0 and reference is not None:
            days = max((reference - match.match_date).total_seconds() / 86400.0, 0.0)
            weight = math.exp(-decay_lambda * days)
        else:
            weight = 1.0
        weighted_points += weight * result_points
        weight_sum += weight

    n = len(considered)
    ppg = points / n if n else 0.0
    ppg_weighted = weighted_points / weight_sum if weight_sum else 0.0

    return FormWindow(
        window=window,
        matches=n,
        wins=wins,
        draws=draws,
        losses=losses,
        points=points,
        goals_for=goals_for,
        goals_against=goals_against,
        goal_difference=goals_for - goals_against,
        win_rate=wins / n if n else 0.0,
        points_per_game=ppg,
        points_per_game_weighted=ppg_weighted,
    )


def compute_form_windows(
    matches: list[Match],
    team_id: str,
    *,
    windows: tuple[int, ...] = DEFAULT_WINDOWS,
    as_of: datetime | None = None,
    decay_lambda: float = 0.0,
) -> TeamFormSummary:
    """Calcula a forma de uma seleção para várias janelas."""
    computed = [
        compute_form(matches, team_id, window=w, as_of=as_of, decay_lambda=decay_lambda)
        for w in windows
    ]
    return TeamFormSummary(team_id=team_id, as_of=as_of, windows=computed)
