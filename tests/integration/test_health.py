"""Testes de integração dos endpoints de saúde."""

from __future__ import annotations

from fastapi.testclient import TestClient

from copamind import __version__


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["version"] == __version__


def test_ready(client: TestClient) -> None:
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"ready": True}

