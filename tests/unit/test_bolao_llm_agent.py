"""Testes do agente LLM do bolao."""

from __future__ import annotations

import json

from copamind.data.repositories import DuckDBRepository
from copamind.llm.client import FakeLLMClient
from copamind.pool.llm_agent import (
    BolaoLLMAgent,
    LLMMatchPick,
    build_combo_pick,
    build_model_consensus_pick,
    classify_local_model,
    run_model_samples,
)


def _pick_json(home: float = 0.5, draw: float = 0.3, away: float = 0.2) -> str:
    return json.dumps(
        {
            "winner": "home",
            "prob_home": home,
            "prob_draw": draw,
            "prob_away": away,
            "predicted_home_goals": 2,
            "predicted_away_goals": 1,
            "goes_to_extra_time": False,
            "goes_to_penalties": False,
            "penalty_winner": "none",
            "first_goal_scorer": None,
            "player_picks": [],
            "confidence": 0.7,
            "rationale": "Baseline estatistico favorece o mandante.",
            "evidence_ids": ["statistical_baseline"],
            "coherence_notes": "Resposta individual.",
        }
    )


def test_classify_local_models() -> None:
    assert classify_local_model("qwen/qwen3.5-9b").model_class == "bolao"
    assert classify_local_model("google/gemma-4-31b-qat").model_class == "heavy"
    assert classify_local_model("google/gemma-4-31b-qat").participates is True
    assert classify_local_model("gemma-4-e4b-it-qat").participates is False
    assert classify_local_model("zai-org/glm-4.7-flash").model_class == "heavy"
    assert classify_local_model("microsoft/phi-4-reasoning-plus").participates is True
    info = classify_local_model("text-embedding-nomic-embed-text-v1.5")
    assert info.model_class == "embedding"
    assert info.participates is False


def test_agent_repairs_invalid_non_json(seeded_repo: DuckDBRepository) -> None:
    matches = seeded_repo.list_finished_matches()
    client = FakeLLMClient({"m1": ["isto nao e json", _pick_json()]})
    result = BolaoLLMAgent(client, "m1").run(seeded_repo, matches[-1])
    assert result.status == "valid"
    assert result.pick is not None
    assert result.pick.predicted_home_goals == 2
    assert len(client.calls) == 2


def test_agent_marks_invalid_after_failed_repair(seeded_repo: DuckDBRepository) -> None:
    matches = seeded_repo.list_finished_matches()
    client = FakeLLMClient({"m1": ["texto", "outro texto"]})
    result = BolaoLLMAgent(client, "m1").run(seeded_repo, matches[-1])
    assert result.status == "invalid"
    assert result.pick is None
    assert "JSON" in (result.error or "")


def test_combo_uses_valid_picks(seeded_repo: DuckDBRepository) -> None:
    match = seeded_repo.list_finished_matches()[-1]
    picks = [
        LLMMatchPick.model_validate(json.loads(_pick_json(0.6, 0.2, 0.2))),
        LLMMatchPick.model_validate(json.loads(_pick_json(0.4, 0.4, 0.2))),
    ]
    combo = build_combo_pick(match, picks)
    assert combo is not None
    assert combo.winner == "home"
    assert combo.predicted_home_goals == 2
    assert abs(combo.prob_home - 0.5) < 1e-6


def test_model_consensus_uses_mode_before_rounding(seeded_repo: DuckDBRepository) -> None:
    match = seeded_repo.list_finished_matches()[-1]
    picks = [
        LLMMatchPick.model_validate(json.loads(_pick_json(0.6, 0.2, 0.2))),
        LLMMatchPick.model_validate(json.loads(_pick_json(0.5, 0.3, 0.2))),
        LLMMatchPick.model_validate(
            json.loads(_pick_json(0.4, 0.3, 0.3))
            | {"predicted_home_goals": 3, "predicted_away_goals": 2}
        ),
    ]
    consensus = build_model_consensus_pick(match, picks)
    assert consensus is not None
    assert consensus.predicted_home_goals == 2
    assert consensus.predicted_away_goals == 1
    assert consensus.coherence_notes


def test_model_consensus_preserves_penalty_prediction(seeded_repo: DuckDBRepository) -> None:
    match = seeded_repo.list_finished_matches()[-1]
    pick = LLMMatchPick.model_validate(json.loads(_pick_json()))
    # Placar empatado → pênaltis são coerentes e devem ser preservados
    pick = pick.model_copy(
        update={
            "predicted_home_goals": 1,
            "predicted_away_goals": 1,
            "goes_to_extra_time": True,
            "goes_to_penalties": True,
            "penalty_winner": "away",
        }
    )

    consensus = build_model_consensus_pick(match, [pick])

    assert consensus is not None
    assert consensus.goes_to_extra_time is True
    assert consensus.goes_to_penalties is True
    assert consensus.penalty_winner == "away"


def test_normalized_pick_strips_penalties_when_score_not_drawn(seeded_repo: DuckDBRepository) -> None:
    """Pênaltis declarados com placar decidido (2-1) devem ser removidos na normalização."""
    match = seeded_repo.list_finished_matches()[-1]
    pick = LLMMatchPick.model_validate(json.loads(_pick_json()))
    # Placar 2-1 mas LLM erroneamente marcou pênaltis
    pick = pick.model_copy(
        update={
            "predicted_home_goals": 2,
            "predicted_away_goals": 1,
            "goes_to_extra_time": True,
            "goes_to_penalties": True,
            "penalty_winner": "away",
        }
    )

    consensus = build_model_consensus_pick(match, [pick])

    assert consensus is not None
    assert consensus.goes_to_extra_time is False
    assert consensus.goes_to_penalties is False
    assert consensus.penalty_winner == "none"


def test_run_model_samples_adds_previous_answers(seeded_repo: DuckDBRepository) -> None:
    match = seeded_repo.list_finished_matches()[-1]
    client = FakeLLMClient({"m1": [_pick_json(), _pick_json(0.4, 0.4, 0.2), _pick_json()]})
    consensus = run_model_samples(client, seeded_repo, match, "m1", round_id="r1", samples=3)
    assert consensus is not None
    assert consensus.valid_samples == 3
    assert len(client.calls) == 3
    second_messages = client.calls[1]["messages"]
    assert isinstance(second_messages, list)
    assert "previous_model_answers" in second_messages[-1]["content"]


def test_run_model_samples_returns_none_when_all_invalid(seeded_repo: DuckDBRepository) -> None:
    match = seeded_repo.list_finished_matches()[-1]
    client = FakeLLMClient(
        {"m1": ["bad", "still bad", "nope", "repair bad", "repair bad", "repair bad"]}
    )
    consensus = run_model_samples(client, seeded_repo, match, "m1", round_id="r1", samples=3)
    assert consensus is None
