"""RAG: chunking, embeddings, armazenamento vetorial e busca híbrida (E5)."""

from copamind.rag.chunk import RagChunk, chunk_user_report
from copamind.rag.embeddings import Embedder, FakeEmbedder, OllamaEmbedder
from copamind.rag.retriever import HybridRetriever, RetrievedChunk, build_grounded_context
from copamind.rag.store import InMemoryVectorStore, VectorStore

__all__ = [
    "Embedder",
    "FakeEmbedder",
    "HybridRetriever",
    "InMemoryVectorStore",
    "OllamaEmbedder",
    "RagChunk",
    "RetrievedChunk",
    "VectorStore",
    "build_grounded_context",
    "chunk_user_report",
]
