"""Testes de integração do RAG (indexação de relatos + API)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from copamind.data.repositories import DuckDBRepository
from copamind.rag.service import RagService
from copamind.reports.service import create_user_report


def test_index_and_search_user_reports(seeded_repo: DuckDBRepository) -> None:
    create_user_report(seeded_repo, "O Brasil venceu o México por 2 a 1 ontem.")
    create_user_report(seeded_repo, "Análise tática: a Argentina jogou no 4-3-3.")
    service = RagService()
    indexed = service.index_user_reports(seeded_repo)
    assert indexed == 2
    results = service.search("Brasil México resultado", top_k=1)
    assert results
    assert "Brasil" in results[0].chunk.text


def test_index_empty(seeded_repo: DuckDBRepository) -> None:
    service = RagService()
    assert service.index_user_reports(seeded_repo) == 0


def test_rag_api_index_and_search(data_client: TestClient) -> None:
    data_client.post("/user-reports", json={"text": "O Brasil venceu o México por 2 a 1."})
    index_resp = data_client.post("/rag/index")
    assert index_resp.status_code == 200
    assert index_resp.json()["indexed"] >= 1

    search_resp = data_client.post("/rag/search", json={"query": "Brasil México", "top_k": 3})
    assert search_resp.status_code == 200
    body = search_resp.json()
    assert body
    assert "chunk" in body[0]

    sources = data_client.get("/rag/sources")
    assert sources.status_code == 200
    assert "user_input" in sources.json()


