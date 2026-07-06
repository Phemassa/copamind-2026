"""Serviço do bolão: trava palpites, registra resultados, pontua e ranqueia."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from copamind.core.logging import get_logger
from copamind.data.repositories import DuckDBRepository
from copamind.data.schemas import Match, MatchStatus, PoolPrediction, PoolResult
from copamind.pool.predictors import Predictor, default_predictors
from copamind.pool.scoring import ScoredPrediction, bolao_points, brier_score, outcome

logger = get_logger(__name__)


class PredictorStanding(BaseModel):
    """Classificação de um preditor no bolão."""

    predictor_name: str
    predictions: int = Field(ge=0)
    total_points: int = Field(ge=0)
    average_points: float = Field(ge=0)
    exact_scores: int = Field(ge=0)
    correct_results: int = Field(ge=0)
    mean_brier: float = Field(ge=0, le=2)


class BacktestSummary(BaseModel):
    """Resumo de uma execução de backtest do bolão."""

    matches_evaluated: int
    predictions_locked: int
    standings: list[PredictorStanding]


def _prediction_id(predictor_name: str, match_id: str) -> str:
    return f"{predictor_name}:{match_id}"


def lock_match_predictions(
    repo: DuckDBRepository,
    match: Match,
    predictors: list[Predictor] | None = None,
) -> list[PoolPrediction]:
    """Trava os palpites dos preditores para uma partida (idempotente por preditor)."""
    predictors = predictors if predictors is not None else default_predictors()
    snapshot_id = repo.latest_snapshot_id() or "adhoc"
    locked_at = datetime.now(UTC)
    locked: list[PoolPrediction] = []
    for predictor in predictors:
        prediction_id = _prediction_id(predictor.name, match.match_id)
        if repo.pool_prediction_exists(prediction_id):
            continue
        data = predictor.predict(repo, match)
        if data is None:
            continue
        prediction = PoolPrediction(
            prediction_id=prediction_id,
            predictor_name=predictor.name,
            match_id=match.match_id,
            snapshot_id=snapshot_id,
            home_team_id=match.home_team_id,
            away_team_id=match.away_team_id,
            prob_home=data.prob_home,
            prob_draw=data.prob_draw,
            prob_away=data.prob_away,
            predicted_home_goals=data.predicted_home_goals,
            predicted_away_goals=data.predicted_away_goals,
            locked_at=locked_at,
        )
        repo.insert_pool_prediction(prediction)
        locked.append(prediction)
    return locked


def record_result(repo: DuckDBRepository, match: Match) -> None:
    """Registra o resultado real de uma partida finalizada."""
    if match.status is not MatchStatus.finished:
        raise ValueError("apenas partidas finalizadas têm resultado")
    if match.home_score is None or match.away_score is None:
        raise ValueError("partida finalizada sem placar")
    repo.upsert_pool_result(
        PoolResult(
            match_id=match.match_id,
            home_score=match.home_score,
            away_score=match.away_score,
            recorded_at=datetime.now(UTC),
        )
    )


def score_all(repo: DuckDBRepository) -> list[ScoredPrediction]:
    """Pontua todos os palpites que já possuem resultado registrado."""
    results = {r.match_id: r for r in repo.list_pool_results()}
    scored: list[ScoredPrediction] = []
    for prediction in repo.list_pool_predictions():
        result = results.get(prediction.match_id)
        if result is None:
            continue
        points = bolao_points(
            prediction.predicted_home_goals,
            prediction.predicted_away_goals,
            result.home_score,
            result.away_score,
        )
        actual = outcome(result.home_score, result.away_score)
        brier = brier_score(
            prediction.prob_home, prediction.prob_draw, prediction.prob_away, actual
        )
        predicted_outcome = outcome(
            prediction.predicted_home_goals, prediction.predicted_away_goals
        )
        scored.append(
            ScoredPrediction(
                predictor_name=prediction.predictor_name,
                match_id=prediction.match_id,
                points=points,
                brier=brier,
                correct_result=predicted_outcome == actual,
                exact_score=(
                    prediction.predicted_home_goals == result.home_score
                    and prediction.predicted_away_goals == result.away_score
                ),
            )
        )
    return scored


def leaderboard(repo: DuckDBRepository) -> list[PredictorStanding]:
    """Agrega os palpites pontuados em uma classificação por preditor."""
    scored = score_all(repo)
    by_predictor: dict[str, list[ScoredPrediction]] = {}
    for item in scored:
        by_predictor.setdefault(item.predictor_name, []).append(item)

    standings: list[PredictorStanding] = []
    for name, items in by_predictor.items():
        n = len(items)
        total = sum(i.points for i in items)
        standings.append(
            PredictorStanding(
                predictor_name=name,
                predictions=n,
                total_points=total,
                average_points=total / n if n else 0.0,
                exact_scores=sum(1 for i in items if i.exact_score),
                correct_results=sum(1 for i in items if i.correct_result),
                mean_brier=sum(i.brier for i in items) / n if n else 0.0,
            )
        )
    standings.sort(key=lambda s: (s.total_points, -s.mean_brier), reverse=True)
    return standings


def run_backtest(
    repo: DuckDBRepository,
    predictors: list[Predictor] | None = None,
) -> BacktestSummary:
    """Simula o bolão sobre o histórico: trava palpites e registra resultados.

    Para cada partida finalizada (em ordem cronológica), os preditores geram
    palpites usando apenas dados anteriores ao apito; em seguida o resultado é
    registrado. Reproduz o "bolão ao vivo" de forma auditável.
    """
    matches = repo.list_finished_matches()
    locked_total = 0
    evaluated = 0
    for match in matches:
        locked = lock_match_predictions(repo, match, predictors)
        if locked:
            evaluated += 1
            locked_total += len(locked)
        record_result(repo, match)
    logger.info("pool_backtest", matches=evaluated, predictions=locked_total)
    return BacktestSummary(
        matches_evaluated=evaluated,
        predictions_locked=locked_total,
        standings=leaderboard(repo),
    )
