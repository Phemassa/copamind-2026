"""Testes de integração de ensemble e calibração (serviço + API)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from copamind.data.repositories import DuckDBRepository
from copamind.models.calibration.report import calibration_report
from copamind.models.ensemble.service import ensemble_match
from copamind.pool.service import run_backtest


def test_ensemble_match(seeded_repo: DuckDBRepository) -> None:
    pred = ensemble_match(seeded_repo, "T-NTL", "T-SDR")
    total = pred.prob_home + pred.prob_draw + pred.prob_away
    assert total == pytest.approx(1.0, abs=1e-6)


def test_calibration_report_after_backtest(seeded_repo: DuckDBRepository) -> None:
    run_backtest(seeded_repo)
    reports = calibration_report(seeded_repo)
    assert reports
    for report in reports:
        assert report.samples > 0
        assert 0.0 <= report.brier <= 2.0
        assert report.reliability


def test_ensemble_api(data_client: TestClient) -> None:
    response = data_client.post(
        "/predictions/ensemble",
        json={"home_team_id": "T-NTL", "away_team_id": "T-SDR"},
    )
    assert response.status_code == 200
    body = response.json()
    total = body["prob_home"] + body["prob_draw"] + body["prob_away"]
    assert abs(total - 1.0) < 1e-6


def test_calibration_api(data_client: TestClient) -> None:
    data_client.post("/pool/backtest")
    response = data_client.get("/pool/calibration")
    assert response.status_code == 200
    assert len(response.json()) >= 1
