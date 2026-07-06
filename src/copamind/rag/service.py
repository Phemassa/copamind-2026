"""Serviço RAG: indexa relatos do usuário e executa busca híbrida."""

from __future__ import annotations

from typing import Any

from copamind.core.logging import get_logger
from copamind.data.repositories import DuckDBRepository
from copamind.rag.chunk import chunk_user_report
from copamind.rag.embeddings import Embedder, FakeEmbedder
from copamind.rag.retriever import HybridRetriever, RetrievedChunk
from copamind.rag.store import InMemoryVectorStore, VectorStore

logger = get_logger(__name__)


class RagService:
    """Fachada do RAG: mantém store, embedder e retriever."""

    def __init__(self, store: VectorStore | None = None, embedder: Embedder | None = None) -> None:
        self._store = store or InMemoryVectorStore()
        self._embedder = embedder or FakeEmbedder()
        self._retriever = HybridRetriever(self._store, self._embedder)

    def index_user_reports(self, repo: DuckDBRepository) -> int:
        """Indexa os relatos atuais do usuário. Retorna quantos foram indexados."""
        chunks = [chunk_user_report(report) for report in repo.list_user_reports()]
        if not chunks:
            return 0
        vectors = self._embedder.embed([c.text for c in chunks])
        self._store.upsert(list(zip(chunks, vectors, strict=True)))
        logger.info("rag_indexed", count=len(chunks))
        return len(chunks)

    def search(
        self,
        query: str,
        *,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[RetrievedChunk]:
        """Busca híbrida sobre o índice."""
        return self._retriever.search(query, top_k=top_k, filters=filters)

    def count(self) -> int:
        """Número de chunks indexados."""
        return self._store.count()

    def sources(self) -> list[str]:
        """Fontes distintas presentes no índice (a partir do que foi buscado)."""
        # Implementação mínima: retorna os tipos de fonte conhecidos.
        return ["user_input"]
