"""Testes dos helpers de chat e calibração do dashboard."""

from __future__ import annotations

import json

from copamind.data.repositories import DuckDBRepository
from copamind.llm.client import FakeLLMClient
from copamind.llm.orchestrator import ModelSpec
from copamind.ui.dashboard import calibration_view, chat_view


def _analyst_json(role: str, team: str) -> str:
    return json.dumps(
        {
            "model_role": role,
            "answer": f"{team} é favorito.",
            "predicted_team": team,
            "confidence": "medium",
            "claims": [],
            "agrees_with_statistical_model": True,
        }
    )


def _auditor_json() -> str:
    return json.dumps(
        {"model_role": "evidence_auditor", "verdicts": [], "data_gaps": [], "notes": "ok"}
    )


def test_calibration_view(seeded_repo: DuckDBRepository) -> None:
    reports = calibration_view(seeded_repo)
    assert reports
    for report in reports:
        assert "reliability" in report
        assert 0.0 <= report["brier"] <= 2.0


def test_chat_view_with_fake_client(seeded_repo: DuckDBRepository) -> None:
    client = FakeLLMClient(
        {
            "analyst": _analyst_json("primary_analyst", "T-NTL"),
            "challenger": _analyst_json("alternative_analysis", "T-NTL"),
            "auditor": _auditor_json(),
        }
    )
    result = chat_view(
        seeded_repo,
        client,
        home_id="T-NTL",
        away_id="T-SDR",
        question="Quem ganha?",
        analyst=ModelSpec(role="primary_analyst", model_id="analyst"),
        challenger=ModelSpec(role="alternative_analysis", model_id="challenger"),
        auditor=ModelSpec(role="evidence_auditor", model_id="auditor"),
    )
    assert len(result["boxes"]) == 3
    assert result["consensus"]["predicted_team"] == "T-NTL"
    assert result["response_language"] == "pt-BR"
