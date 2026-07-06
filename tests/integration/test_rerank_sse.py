"""Testes do reranker e do gerador de eventos (SSE) do orquestrador."""

from __future__ import annotations

import json

from copamind.data.repositories import DuckDBRepository
from copamind.llm.client import FakeLLMClient
from copamind.llm.orchestrator import (
    ModelSpec,
    SequentialOrchestrator,
    build_evidence_pack,
)
from copamind.rag.chunk import RagChunk
from copamind.rag.embeddings import FakeEmbedder
from copamind.rag.retriever import HybridRetriever, LexicalReranker
from copamind.rag.store import InMemoryVectorStore


def _analyst_json(role: str, team: str) -> str:
    return json.dumps({"model_role": role, "answer": f"{team} favorito.", "predicted_team": team})


def _auditor_json() -> str:
    return json.dumps({"model_role": "evidence_auditor", "verdicts": []})


def test_reranker_changes_order() -> None:
    emb = FakeEmbedder()
    store = InMemoryVectorStore()
    chunks = [
        RagChunk(chunk_id="c1", document_id="c1", text="clima e turismo no país"),
        RagChunk(chunk_id="c2", document_id="c2", text="Brasil venceu o México por 2 a 1"),
    ]
    store.upsert(list(zip(chunks, emb.embed([c.text for c in chunks]), strict=True)))
    reranker = LexicalReranker()
    retriever = HybridRetriever(store, emb, reranker=reranker)
    results = retriever.search("Brasil México placar", top_k=2)
    # O reranker lexical deve trazer o chunk com sobreposição de termos ao topo.
    assert results[0].chunk.chunk_id == "c2"


def test_run_events_sequence(seeded_repo: DuckDBRepository) -> None:
    client = FakeLLMClient(
        {
            "analyst": _analyst_json("primary_analyst", "T-BRA"),
            "challenger": _analyst_json("alternative_analysis", "T-BRA"),
            "auditor": _auditor_json(),
        }
    )
    orchestrator = SequentialOrchestrator(
        client,
        ModelSpec(role="primary_analyst", model_id="analyst"),
        ModelSpec(role="alternative_analysis", model_id="challenger"),
        ModelSpec(role="evidence_auditor", model_id="auditor"),
    )
    pack = build_evidence_pack(seeded_repo, "T-BRA", "T-FRA")
    events = list(orchestrator.run_events("Quem ganha?", pack))
    names = [e["event"] for e in events]
    assert names == ["understanding", "analyst", "challenger", "auditor", "consensus"]
    assert events[-1]["consensus"]["predicted_team"] == "T-BRA"

