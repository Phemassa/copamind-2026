"""Rotas do RAG (MASTER_PLAN §20)."""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from copamind.api.dependencies import get_repository
from copamind.data.repositories import DuckDBRepository
from copamind.rag.retriever import RetrievedChunk
from copamind.rag.service import RagService

router = APIRouter(tags=["rag"], prefix="/rag")

RepoDep = Annotated[DuckDBRepository, Depends(get_repository)]


@lru_cache(maxsize=1)
def _rag_service() -> RagService:
    """Serviço RAG singleton do processo (índice em memória)."""
    return RagService()


class IndexResponse(BaseModel):
    """Resposta da indexação."""

    indexed: int
    total: int


class SearchRequest(BaseModel):
    """Corpo da busca RAG."""

    query: str
    top_k: int = 5
    filters: dict[str, Any] | None = None


@router.post("/index", response_model=IndexResponse)
def index(repo: RepoDep) -> IndexResponse:
    """Indexa os relatos do usuário no índice vetorial."""
    service = _rag_service()
    indexed = service.index_user_reports(repo)
    return IndexResponse(indexed=indexed, total=service.count())


@router.post("/search", response_model=list[RetrievedChunk])
def search(request: SearchRequest) -> list[RetrievedChunk]:
    """Busca híbrida sobre o índice."""
    return _rag_service().search(request.query, top_k=request.top_k, filters=request.filters)


@router.get("/sources", response_model=list[str])
def sources() -> list[str]:
    """Lista as fontes presentes no índice."""
    return _rag_service().sources()
