"""Testes de integração das rotas de dados."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_list_teams(data_client: TestClient) -> None:
    response = data_client.get("/teams")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 48


def test_get_team(data_client: TestClient) -> None:
    response = data_client.get("/teams/T-BRA")
    assert response.status_code == 200
    assert response.json()["name"] == "Brasil"


def test_get_team_not_found(data_client: TestClient) -> None:
    response = data_client.get("/teams/nope")
    assert response.status_code == 404


def test_list_matches(data_client: TestClient) -> None:
    response = data_client.get("/matches")
    assert response.status_code == 200
    assert len(response.json()) == 92


def test_last_matches(data_client: TestClient) -> None:
    response = data_client.get("/teams/T-BRA/last-matches?limit=3")
    assert response.status_code == 200
    assert len(response.json()) == 3


def test_team_form(data_client: TestClient) -> None:
    response = data_client.get("/teams/T-BRA/form")
    assert response.status_code == 200
    body = response.json()
    assert body["team_id"] == "T-BRA"
    assert isinstance(body["elo_rating"], float)
    assert [w["window"] for w in body["form"]["windows"]] == [5, 10, 15]


def test_team_form_not_found(data_client: TestClient) -> None:
    response = data_client.get("/teams/nope/form")
    assert response.status_code == 404


