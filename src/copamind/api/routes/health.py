"""Rotas de saúde e prontidão (MASTER_PLAN §20)."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from copamind import __version__

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Resposta do endpoint de saúde."""

    status: str
    version: str


class ReadyResponse(BaseModel):
    """Resposta do endpoint de prontidão."""

    ready: bool


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Liveness check: indica que o processo está no ar."""
    return HealthResponse(status="ok", version=__version__)


@router.get("/ready", response_model=ReadyResponse)
def ready() -> ReadyResponse:
    """Readiness check: indica que a aplicação está pronta para receber tráfego.

    Na Fase 0 não há dependências obrigatórias; sempre retorna pronto.
    Fases posteriores validarão DuckDB, Qdrant e LM Studio aqui.
    """
    return ReadyResponse(ready=True)
