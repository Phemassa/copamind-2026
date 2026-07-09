"""Testes de integração do repositório DuckDB."""

from __future__ import annotations

from datetime import UTC, datetime

from copamind.data.repositories import DuckDBRepository
from copamind.data.schemas import MatchStatus, PoolPrediction


def test_seeded_counts(seeded_repo: DuckDBRepository) -> None:
    assert seeded_repo.count("teams") == 48
    assert seeded_repo.count("matches") == 92
    assert seeded_repo.count("snapshots") == 1


def test_create_schema_idempotent(seeded_repo: DuckDBRepository) -> None:
    # Chamar novamente não deve falhar nem duplicar dados.
    seeded_repo.create_schema()
    assert seeded_repo.count("teams") == 48


def test_list_and_get_team(seeded_repo: DuckDBRepository) -> None:
    teams = seeded_repo.list_teams()
    assert len(teams) == 48
    team = seeded_repo.get_team("T-BRA")
    assert team is not None
    assert team.fifa_code == "BRA"
    assert seeded_repo.get_team("inexistente") is None


def test_last_matches_ordering(seeded_repo: DuckDBRepository) -> None:
    matches = seeded_repo.get_last_matches("T-BRA", limit=3)
    assert len(matches) == 3
    dates = [m.match_date for m in matches]
    assert dates == sorted(dates, reverse=True)
    assert all(m.status is MatchStatus.finished for m in matches)


def test_last_matches_as_of_prevents_leakage(seeded_repo: DuckDBRepository) -> None:
    # Antes de qualquer partida disponível, não deve retornar nada.
    early = datetime(2024, 1, 1)
    assert seeded_repo.get_last_matches("T-BRA", as_of=early) == []


def test_upsert_is_idempotent(seeded_repo: DuckDBRepository) -> None:
    before = seeded_repo.count("teams")
    teams = seeded_repo.list_teams()
    seeded_repo.upsert_teams(teams)  # reprocessar não duplica (PK)
    assert seeded_repo.count("teams") == before


def test_llm_round_persistence(seeded_repo: DuckDBRepository) -> None:
    now = datetime.now(UTC)
    seeded_repo.insert_llm_pool_round(
        "round-1",
        "match-1",
        now,
        "running",
        3,
        ["m1"],
    )
    seeded_repo.insert_llm_model_run(
        run_id="run-1",
        round_id="round-1",
        match_id="match-1",
        model_id="m1",
        predictor_name="llm:m1:round:round-1",
        sample_index=1,
        prompt_tokens=10,
        completion_tokens=20,
        latency_ms=1000.0,
        raw_response="{}",
        valid=True,
        error=None,
        attempts=[{"mode": "json_schema", "ok": True}],
        pick={"winner": "home"},
        created_at=now,
    )
    seeded_repo.upsert_llm_model_consensus(
        consensus_id="round-1:m1",
        round_id="round-1",
        match_id="match-1",
        model_id="m1",
        predictor_name="llm:m1:round:round-1",
        valid_samples=1,
        total_samples=3,
        prob_home=0.5,
        prob_draw=0.3,
        prob_away=0.2,
        predicted_home_goals=2,
        predicted_away_goals=1,
        winner="home",
        first_goal_scorer="Atacante",
        coherence_score=0.8,
        coherence_notes="Alta coerencia",
        payload={"pick": "ok"},
        created_at=now,
    )
    seeded_repo.update_llm_pool_round_status("round-1", "completed")

    rounds = seeded_repo.list_llm_pool_rounds()
    runs = seeded_repo.list_llm_model_runs("round-1")
    consensus = seeded_repo.list_llm_model_consensus("round-1")
    metrics = seeded_repo.llm_model_metrics()

    assert seeded_repo.count("llm_pool_rounds") == 1
    assert rounds[0]["selected_models"] == ["m1"]
    assert runs[0]["attempts"][0]["ok"] is True
    assert consensus[0]["payload"] == {"pick": "ok"}
    assert metrics[0]["model_id"] == "m1"


def test_llm_phase_batch_persistence(seeded_repo: DuckDBRepository) -> None:
    now = datetime.now(UTC)
    seeded_repo.insert_llm_phase_batch(
        "batch-1",
        "round_of_16",
        now,
        "running",
        2,
        ["m1", "m2"],
    )
    seeded_repo.insert_llm_pool_round(
        "round-batch-1",
        "match-1",
        now,
        "completed",
        3,
        ["m1"],
        batch_id="batch-1",
        phase="round_of_16",
    )
    seeded_repo.update_llm_phase_batch_status("batch-1", "completed")

    batches = seeded_repo.list_llm_phase_batches()
    rounds = seeded_repo.list_llm_pool_rounds(batch_id="batch-1")

    assert seeded_repo.count("llm_phase_batches") == 1
    assert batches[0]["selected_models"] == ["m1", "m2"]
    assert batches[0]["status"] == "completed"
    assert rounds[0]["batch_id"] == "batch-1"
    assert rounds[0]["phase"] == "round_of_16"


def test_match_feature_snapshot_persistence(seeded_repo: DuckDBRepository) -> None:
    now = datetime.now(UTC)
    seeded_repo.upsert_match_feature_snapshot(
        snapshot_id="feat-1",
        match_id="match-1",
        phase="round_of_16",
        as_of=now,
        features={"fixture": {"match_id": "match-1"}},
        baseline={"available": False},
        created_at=now,
    )

    rows = seeded_repo.list_match_feature_snapshots(phase="round_of_16")

    assert seeded_repo.count("match_feature_snapshots") == 1
    assert rows[0]["snapshot_id"] == "feat-1"
    assert rows[0]["features"]["fixture"]["match_id"] == "match-1"
    assert rows[0]["baseline"] == {"available": False}


def test_reset_llm_history_removes_orphan_phase_predictions(
    seeded_repo: DuckDBRepository,
) -> None:
    now = datetime.now(UTC)
    match = seeded_repo.list_matches()[0]
    llm_prediction = PoolPrediction(
        prediction_id="llm:m1:round:missing-round",
        predictor_name="llm:m1:round:missing-round",
        match_id=match.match_id,
        snapshot_id="snapshot-1",
        home_team_id=match.home_team_id,
        away_team_id=match.away_team_id,
        prob_home=0.5,
        prob_draw=0.25,
        prob_away=0.25,
        predicted_home_goals=2,
        predicted_away_goals=1,
        locked_at=now,
    )
    baseline_prediction = llm_prediction.model_copy(
        update={
            "prediction_id": "elo:orphan-reset-control",
            "predictor_name": "elo",
        }
    )
    seeded_repo.insert_pool_prediction(llm_prediction)
    seeded_repo.insert_pool_prediction(baseline_prediction)
    seeded_repo.upsert_pool_prediction_payload(
        llm_prediction.prediction_id,
        llm_prediction.predictor_name,
        match.match_id,
        {"winner": "home"},
        now,
    )

    deleted = seeded_repo.reset_llm_history(phase=match.stage)

    assert deleted["pool_predictions"] == 1
    assert deleted["pool_prediction_payloads"] == 1
    assert seeded_repo.count("pool_predictions") == 1
    assert seeded_repo.list_pool_predictions()[0].predictor_name == "elo"


