"""Embeddings para o RAG.

`FakeEmbedder` é determinístico (hashing de tokens) e permite testes offline.
`OllamaEmbedder` usa um modelo real (ex.: bge-m3) servido pelo Ollama.
"""

from __future__ import annotations

import hashlib
import math
import re
from typing import Protocol

import httpx

_TOKEN_RE = re.compile(r"\w+", re.UNICODE)


def tokenize(text: str) -> list[str]:
    """Tokeniza um texto em palavras minúsculas."""
    return _TOKEN_RE.findall(text.lower())


def _normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in vector))
    if norm == 0:
        return vector
    return [v / norm for v in vector]


class Embedder(Protocol):
    """Interface de um gerador de embeddings."""

    dimension: int

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Gera vetores para uma lista de textos."""
        ...


class FakeEmbedder:
    """Embedder determinístico por hashing de tokens (bag-of-hashed-words)."""

    def __init__(self, dimension: int = 64) -> None:
        self.dimension = dimension

    def _vectorize(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        for token in tokenize(text):
            digest = hashlib.md5(token.encode("utf-8")).hexdigest()
            index = int(digest, 16) % self.dimension
            vector[index] += 1.0
        return _normalize(vector)

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._vectorize(text) for text in texts]


class OllamaEmbedder:
    """Embedder via Ollama (ex.: modelo bge-m3)."""

    def __init__(
        self,
        model_id: str = "bge-m3",
        base_url: str = "http://localhost:11434",
        dimension: int = 1024,
        timeout: float = 60.0,
    ) -> None:
        self.model_id = model_id
        self.dimension = dimension
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            response = httpx.post(
                f"{self._base_url}/api/embeddings",
                json={"model": self.model_id, "prompt": text},
                timeout=self._timeout,
            )
            response.raise_for_status()
            vectors.append([float(v) for v in response.json()["embedding"]])
        return vectors
