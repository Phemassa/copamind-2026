"""Testes de integração do orquestrador e do benchmark (com cliente fake)."""

from __future__ import annotations

import json

from copamind.data.repositories import DuckDBRepository
from copamind.llm.benchmark import benchmark_models
from copamind.llm.client import FakeLLMClient
from copamind.llm.orchestrator import (
    ModelSpec,
    SequentialOrchestrator,
    build_evidence_pack,
)


def _analyst_json(role: str, team: str, *, grounded: bool = True) -> str:
    return json.dumps(
        {
            "model_role": role,
            "response_language": "pt-BR",
            "answer": f"{team} é favorito.",
            "predicted_team": team,
            "confidence": "medium",
            "claims": [
                {
                    "text": "Boa forma recente.",
                    "evidence_ids": ["form:x"] if grounded else [],
                }
            ],
            "agrees_with_statistical_model": True,
        }
    )


def _auditor_json() -> str:
    return json.dumps(
        {
            "model_role": "evidence_auditor",
            "verdicts": [{"text": "Boa forma recente.", "status": "supported"}],
            "data_gaps": [],
            "notes": "ok",
        }
    )


def _orchestrator(client: FakeLLMClient) -> SequentialOrchestrator:
    return SequentialOrchestrator(
        client,
        analyst=ModelSpec(role="primary_analyst", model_id="analyst"),
        challenger=ModelSpec(role="alternative_analysis", model_id="challenger"),
        auditor=ModelSpec(role="evidence_auditor", model_id="auditor"),
    )


def test_evidence_pack(seeded_repo: DuckDBRepository) -> None:
    pack = build_evidence_pack(seeded_repo, "T-BRA", "T-FRA")
    assert pack.statistical_pick in {"T-BRA", "T-FRA"}
    total = sum(pack.statistical_prediction.values())
    assert abs(total - 1.0) < 1e-6
    assert "prediction:poisson" in pack.evidence_ids


def test_orchestration_agreement(seeded_repo: DuckDBRepository) -> None:
    client = FakeLLMClient(
        {
            "analyst": _analyst_json("primary_analyst", "T-BRA"),
            "challenger": _analyst_json("alternative_analysis", "T-BRA"),
            "auditor": _auditor_json(),
        }
    )
    pack = build_evidence_pack(seeded_repo, "T-BRA", "T-FRA")
    result = _orchestrator(client).run("Quem ganha?", pack)
    assert len(result.boxes) == 3
    assert result.consensus.predicted_team == "T-BRA"
    assert result.consensus.agreements
    # Modelos foram descarregados (execução sequencial).
    assert set(client.unloaded) == {"analyst", "challenger", "auditor"}


def test_orchestration_handles_model_failure(seeded_repo: DuckDBRepository) -> None:
    client = FakeLLMClient(
        {
            "analyst": "isto não é json",
            "challenger": _analyst_json("alternative_analysis", "T-FRA"),
            "auditor": _auditor_json(),
        }
    )
    pack = build_evidence_pack(seeded_repo, "T-BRA", "T-FRA")
    result = _orchestrator(client).run("Quem ganha?", pack)
    analyst_box = result.boxes[0]
    assert analyst_box.error is not None
    # A sessão continua e o consenso é produzido mesmo com uma falha.
    assert result.consensus.predicted_team is not None
    assert any("falhou" in u for u in result.consensus.uncertainties)


def test_benchmark_models(seeded_repo: DuckDBRepository) -> None:
    client = FakeLLMClient(
        {
            "analyst": _analyst_json("primary_analyst", "T-BRA", grounded=True),
            "challenger": _analyst_json("alternative_analysis", "T-BRA", grounded=False),
        }
    )
    pack = build_evidence_pack(seeded_repo, "T-BRA", "T-FRA")
    specs = [
        ModelSpec(role="primary_analyst", model_id="analyst"),
        ModelSpec(role="alternative_analysis", model_id="challenger"),
    ]
    rows = benchmark_models(client, specs, "Quem ganha?", pack)
    assert len(rows) == 2
    assert all(r.schema_valid for r in rows)
    grounded = {r.model_id: r.grounded_ratio for r in rows}
    assert grounded["analyst"] == 1.0
    assert grounded["challenger"] == 0.0


