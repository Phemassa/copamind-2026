"""Testes de integração das rotas de dados."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_list_teams(data_client: TestClient) -> None:
    response = data_client.get("/teams")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 4
    assert {t["fifa_code"] for t in body} == {"NTL", "SDR", "EST", "WST"}


def test_get_team(data_client: TestClient) -> None:
    response = data_client.get("/teams/T-NTL")
    assert response.status_code == 200
    assert response.json()["name"] == "Nortlândia"


def test_get_team_not_found(data_client: TestClient) -> None:
    response = data_client.get("/teams/nope")
    assert response.status_code == 404


def test_list_matches(data_client: TestClient) -> None:
    response = data_client.get("/matches")
    assert response.status_code == 200
    assert len(response.json()) == 20


def test_last_matches(data_client: TestClient) -> None:
    response = data_client.get("/teams/T-NTL/last-matches?limit=3")
    assert response.status_code == 200
    assert len(response.json()) == 3
