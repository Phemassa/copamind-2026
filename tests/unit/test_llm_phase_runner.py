"""Testes do runner de fase das LLMs."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from copamind.data.repositories import DuckDBRepository
from copamind.llm.client import FakeLLMClient
from scripts import run_llm_phase_benchmark as runner


def _pick_json(home_goals: int = 2, away_goals: int = 1) -> str:
    return json.dumps(
        {
            "winner": "home",
            "prob_home": 0.6,
            "prob_draw": 0.2,
            "prob_away": 0.2,
            "predicted_home_goals": home_goals,
            "predicted_away_goals": away_goals,
            "goes_to_extra_time": False,
            "goes_to_penalties": False,
            "penalty_winner": "none",
            "first_goal_scorer": None,
            "player_picks": [],
            "confidence": 0.7,
            "rationale": "Contexto estatistico favorece o mandante.",
            "evidence_ids": ["statistical_baseline"],
            "coherence_notes": "Resposta individual.",
        }
    )


def test_model_first_groups_preserve_model_order(seeded_repo: DuckDBRepository) -> None:
    matches = seeded_repo.list_finished_matches()[:3]
    groups = runner._model_first_groups(
        ["m1", "m2", "m3"],
        [
            (matches[0], ["m2", "m1"]),
            (matches[1], ["m1"]),
            (matches[2], ["m2"]),
        ],
    )

    assert [(model_id, [match.match_id for match in model_matches]) for model_id, model_matches in groups] == [
        ("m1", [matches[0].match_id, matches[1].match_id]),
        ("m2", [matches[0].match_id, matches[2].match_id]),
    ]


def test_model_first_runner_saves_each_call_and_unloads_once(seeded_repo: DuckDBRepository, monkeypatch) -> None:
    matches = seeded_repo.list_finished_matches()[:2]
    remaining = [(matches[0], ["m1", "m2"]), (matches[1], ["m1"])]
    client = FakeLLMClient({"m1": [_pick_json(), _pick_json(1, 0)], "m2": [_pick_json(0, 1)]})
    monkeypatch.setattr(runner, "write_llm_phase_progress", lambda *_args, **_kwargs: {})
    batch_id = "batch-model-first"
    seeded_repo.insert_llm_phase_batch(batch_id, "quarterfinal", datetime.now(UTC), "running", 2, ["m1", "m2"])
    rounds = runner._create_match_rounds(seeded_repo, remaining, batch_id, "quarterfinal", 1)
    progress: dict[str, object] = {
        "batch_id": batch_id,
        "phase": "quarterfinal",
        "started_monotonic": 0.0,
        "started_at": datetime.now(UTC).isoformat(),
        "completed_calls": 0,
        "total_calls": 3,
        "total_matches": 2,
        "total_models": 2,
        "total_samples": 1,
    }

    for model_index, (model_id, model_matches) in enumerate(runner._model_first_groups(["m1", "m2"], remaining), 1):
        for match_index, match in enumerate(model_matches, 1):
            runner._run_model_match(
                seeded_repo,
                client,
                match,
                model_id,
                round_id=rounds[match.match_id],
                samples=1,
                model_index=model_index,
                total_models=2,
                match_index=match_index,
                total_matches=2,
                progress=progress,
            )
        client.unload(model_id)
    runner._finalize_match_rounds(seeded_repo, remaining, rounds)

    assert [call["model_id"] for call in client.calls] == ["m1", "m1", "m2"]
    assert client.unloaded == ["m1", "m2"]
    assert seeded_repo.count("llm_model_runs") == 3
    assert seeded_repo.count("llm_model_consensus") == 3
    assert all(row["status"] == "completed" for row in seeded_repo.list_llm_pool_rounds(batch_id=batch_id))
