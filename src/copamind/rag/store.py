"""Armazenamento vetorial do RAG.

`InMemoryVectorStore` (offline, testável) e `QdrantStore` (real, opcional).
Ambos suportam filtros por metadados na busca.
"""

from __future__ import annotations

import math
from typing import Any, Protocol

from copamind.rag.chunk import RagChunk


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Similaridade do cosseno entre dois vetores."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def matches_filters(chunk: RagChunk, filters: dict[str, Any] | None) -> bool:
    """Verifica se um chunk satisfaz filtros de metadados simples."""
    if not filters:
        return True
    for key, value in filters.items():
        actual = getattr(chunk, key, None)
        if isinstance(actual, list):
            if value not in actual:
                return False
        elif actual != value:
            return False
    return True


class VectorStore(Protocol):
    """Interface de um armazenamento vetorial."""

    def upsert(self, items: list[tuple[RagChunk, list[float]]]) -> None:
        """Insere ou atualiza chunks com seus vetores."""
        ...

    def search(
        self,
        query_vector: list[float],
        top_k: int,
        filters: dict[str, Any] | None = None,
    ) -> list[tuple[RagChunk, float]]:
        """Retorna os chunks mais similares (com score de similaridade)."""
        ...

    def count(self) -> int:
        """Número de chunks armazenados."""
        ...


class InMemoryVectorStore:
    """Store vetorial em memória (busca por similaridade do cosseno)."""

    def __init__(self) -> None:
        self._items: dict[str, tuple[RagChunk, list[float]]] = {}

    def upsert(self, items: list[tuple[RagChunk, list[float]]]) -> None:
        for chunk, vector in items:
            self._items[chunk.chunk_id] = (chunk, vector)

    def search(
        self,
        query_vector: list[float],
        top_k: int,
        filters: dict[str, Any] | None = None,
    ) -> list[tuple[RagChunk, float]]:
        scored = [
            (chunk, cosine_similarity(query_vector, vector))
            for chunk, vector in self._items.values()
            if matches_filters(chunk, filters)
        ]
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:top_k]

    def count(self) -> int:
        return len(self._items)


class QdrantStore:
    """Store vetorial usando Qdrant (real; requer o extra `rag` e servidor ativo)."""

    def __init__(
        self,
        collection: str = "copamind_knowledge",
        url: str = "http://localhost:6333",
        dimension: int = 1024,
    ) -> None:
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams
        except ImportError as exc:  # pragma: no cover - depende do extra 'rag'
            raise RuntimeError(
                "pacote 'qdrant-client' não instalado. Instale com: pip install -e '.[rag]'"
            ) from exc
        self._collection = collection
        self._client = QdrantClient(url=url)
        if not self._client.collection_exists(collection):
            self._client.create_collection(
                collection_name=collection,
                vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
            )

    def upsert(self, items: list[tuple[RagChunk, list[float]]]) -> None:  # pragma: no cover
        import uuid

        from qdrant_client.models import PointStruct

        points = [
            PointStruct(
                id=str(uuid.uuid5(uuid.NAMESPACE_URL, chunk.chunk_id)),
                vector=vector,
                payload=chunk.model_dump(mode="json"),
            )
            for chunk, vector in items
        ]
        self._client.upsert(collection_name=self._collection, points=points)

    def search(  # pragma: no cover
        self,
        query_vector: list[float],
        top_k: int,
        filters: dict[str, Any] | None = None,
    ) -> list[tuple[RagChunk, float]]:
        hits = self._client.query_points(
            collection_name=self._collection,
            query=query_vector,
            limit=top_k * 5,
        ).points
        results: list[tuple[RagChunk, float]] = []
        for hit in hits:
            chunk = RagChunk.model_validate(hit.payload)
            if matches_filters(chunk, filters):
                results.append((chunk, float(hit.score)))
        return results[:top_k]

    def count(self) -> int:  # pragma: no cover
        return int(self._client.count(collection_name=self._collection).count)
