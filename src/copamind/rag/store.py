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
