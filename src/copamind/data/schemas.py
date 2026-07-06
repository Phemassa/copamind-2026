"""Schemas de domínio (Pydantic v2) — MASTER_PLAN §9.

Toda entidade com origem de dados carrega os campos de linhagem
(``source``, ``collected_at``, ``available_at``, ``snapshot_id``) para garantir
reprodutibilidade e prevenção de vazamento temporal (MASTER_PLAN §5.3 e §18).
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class Confederation(StrEnum):
    """Confederações da FIFA."""

    afc = "AFC"
    caf = "CAF"
    concacaf = "CONCACAF"
    conmebol = "CONMEBOL"
    ofc = "OFC"
    uefa = "UEFA"


class MatchStage(StrEnum):
    """Fase da partida."""

    friendly = "friendly"
    qualifier = "qualifier"
    group = "group"
    round_of_32 = "round_of_32"
    round_of_16 = "round_of_16"
    quarterfinal = "quarterfinal"
    semifinal = "semifinal"
    third_place = "third_place"
    final = "final"


class MatchStatus(StrEnum):
    """Situação da partida."""

    scheduled = "scheduled"
    finished = "finished"
    cancelled = "cancelled"


class LineageMixin(BaseModel):
    """Campos de linhagem obrigatórios em dados com origem externa."""

    model_config = ConfigDict(extra="forbid")

    source: str = Field(min_length=1, description="Origem do dado.")
    collected_at: datetime = Field(description="Quando o dado foi coletado.")
    available_at: datetime = Field(
        description="Quando o dado passou a estar disponível (anti-leakage).",
    )
    snapshot_id: str = Field(min_length=1, description="Identificador do snapshot.")


class Team(LineageMixin):
    """Seleção nacional (MASTER_PLAN §9.1)."""

    team_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    fifa_code: str = Field(min_length=2, max_length=3)
    country: str = Field(min_length=1)
    confederation: Confederation
    fifa_ranking: int | None = Field(default=None, ge=1)
    elo_rating: float | None = Field(default=None, gt=0)
    active: bool = True


class Coach(LineageMixin):
    """Técnico de uma seleção."""

    coach_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    nationality: str = Field(min_length=1)
    team_id: str = Field(min_length=1)
    started_at: datetime | None = None
    ended_at: datetime | None = None


class Player(LineageMixin):
    """Jogador de uma seleção."""

    player_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    national_team_id: str = Field(min_length=1)
    position: str | None = None
    active: bool = True


class Match(LineageMixin):
    """Partida entre duas seleções (MASTER_PLAN §9.1)."""

    match_id: str = Field(min_length=1)
    competition: str = Field(min_length=1)
    stage: MatchStage
    match_date: datetime
    home_team_id: str = Field(min_length=1)
    away_team_id: str = Field(min_length=1)
    neutral_venue: bool = False
    home_score: int | None = Field(default=None, ge=0)
    away_score: int | None = Field(default=None, ge=0)
    status: MatchStatus = MatchStatus.scheduled
    importance_weight: float = Field(default=1.0, gt=0)

    def model_post_init(self, _context: object) -> None:
        """Valida invariantes que dependem de múltiplos campos."""
        if self.home_team_id == self.away_team_id:
            raise ValueError("home_team_id e away_team_id não podem ser iguais")
        if self.status is MatchStatus.finished and (
            self.home_score is None or self.away_score is None
        ):
            raise ValueError("partida finalizada exige home_score e away_score")


class Snapshot(BaseModel):
    """Snapshot versionado de dados (MASTER_PLAN §5.3)."""

    model_config = ConfigDict(extra="forbid")

    snapshot_id: str = Field(min_length=1)
    created_at: datetime
    description: str = ""
    dataset_version: str = Field(default="0.1.0")


class Prediction(BaseModel):
    """Previsão de partida produzida por um modelo (MASTER_PLAN §9.1)."""

    model_config = ConfigDict(extra="forbid")

    prediction_id: str = Field(min_length=1)
    snapshot_id: str = Field(min_length=1)
    match_id: str | None = None
    model_name: str = Field(min_length=1)
    model_version: str = Field(min_length=1)
    home_team_id: str = Field(min_length=1)
    away_team_id: str = Field(min_length=1)
    home_win_probability: float = Field(ge=0, le=1)
    draw_probability: float = Field(ge=0, le=1)
    away_win_probability: float = Field(ge=0, le=1)
    expected_home_goals: float = Field(ge=0)
    expected_away_goals: float = Field(ge=0)
    created_at: datetime
