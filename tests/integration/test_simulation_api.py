"""Testes de integração da simulação (serviço + API)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from copamind.data.repositories import DuckDBRepository
from copamind.simulation.service import build_default_config, run_simulation


def test_run_simulation_service(seeded_repo: DuckDBRepository) -> None:
    config = build_default_config(seeded_repo, iterations=1000)
    result = run_simulation(seeded_repo, config)
    assert result.iterations == 1000
    total = sum(t.champion_probability for t in result.teams)
    assert total == pytest.approx(1.0, abs=1e-9)


def test_simulate_api(data_client: TestClient) -> None:
    response = data_client.post("/simulations", json={"iterations": 500})
    assert response.status_code == 200
    body = response.json()
    assert body["iterations"] == 500
    total = sum(t["champion_probability"] for t in body["teams"])
    assert abs(total - 1.0) < 1e-9


def test_simulate_api_invalid_groups(data_client: TestClient) -> None:
    # 1 classificado não é potência de 2 => configuração inválida.
    response = data_client.post(
        "/simulations",
        json={
            "iterations": 100,
            "advance_per_group": 1,
            "groups": {"A": ["T-BRA", "T-FRA", "T-ENG"]},
        },
    )
    assert response.status_code == 422


