"""Serviço de previsão de partidas com o modelo Poisson/Dixon-Coles.

Ajusta o modelo com as partidas finalizadas do repositório, produz a previsão
e a persiste (com linhagem de snapshot). O LLM não participa deste cálculo.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from copamind.data.repositories import DuckDBRepository
from copamind.data.schemas import Prediction
from copamind.models.poisson import MatchPrediction, PoissonModel

MODEL_NAME = "poisson-dixon-coles"
MODEL_VERSION = "0.1.0"


def build_poisson(repo: DuckDBRepository, *, as_of: datetime | None = None) -> PoissonModel:
    """Constrói e ajusta o modelo Poisson com as partidas finalizadas."""
    model = PoissonModel()
    model.fit(repo.list_finished_matches(as_of=as_of))
    return model


def predict_match(
    repo: DuckDBRepository,
    home_id: str,
    away_id: str,
    *,
    neutral_venue: bool = False,
    persist: bool = True,
    as_of: datetime | None = None,
) -> MatchPrediction:
    """Prediz uma partida e opcionalmente persiste o resultado."""
    model = build_poisson(repo, as_of=as_of)
    prediction = model.predict_match(home_id, away_id, neutral_venue=neutral_venue)

    if persist:
        snapshot_id = repo.latest_snapshot_id() or "adhoc"
        repo.upsert_prediction(
            Prediction(
                prediction_id=str(uuid.uuid4()),
                snapshot_id=snapshot_id,
                match_id=None,
                model_name=MODEL_NAME,
                model_version=MODEL_VERSION,
                home_team_id=home_id,
                away_team_id=away_id,
                home_win_probability=prediction.prob_home_win,
                draw_probability=prediction.prob_draw,
                away_win_probability=prediction.prob_away_win,
                expected_home_goals=prediction.expected_home_goals,
                expected_away_goals=prediction.expected_away_goals,
                created_at=datetime.now(UTC),
            )
        )
    return prediction
