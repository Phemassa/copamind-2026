"""RAG: chunking, embeddings, armazenamento vetorial e busca híbrida (E5)."""

from copamind.rag.chunk import RagChunk, chunk_user_report
from copamind.rag.embeddings import Embedder, FakeEmbedder, OllamaEmbedder
from copamind.rag.retriever import (
    HybridRetriever,
    LexicalReranker,
    Reranker,
    RetrievedChunk,
    build_grounded_context,
)
from copamind.rag.store import InMemoryVectorStore, QdrantStore, VectorStore

__all__ = [
    "Embedder",
    "FakeEmbedder",
    "HybridRetriever",
    "InMemoryVectorStore",
    "LexicalReranker",
    "OllamaEmbedder",
    "QdrantStore",
    "RagChunk",
    "Reranker",
    "RetrievedChunk",
    "VectorStore",
    "build_grounded_context",
    "chunk_user_report",
]
