"""Rotas de chat com streaming SSE (MASTER_PLAN §20, §21.3)."""

from __future__ import annotations

import json
from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from copamind.api.dependencies import get_repository
from copamind.core.config import get_settings
from copamind.data.repositories import DuckDBRepository
from copamind.llm.client import LMStudioClient
from copamind.llm.config import load_model_specs
from copamind.llm.orchestrator import SequentialOrchestrator, build_evidence_pack

router = APIRouter(tags=["chat"], prefix="/chat")

RepoDep = Annotated[DuckDBRepository, Depends(get_repository)]


class ChatRequest(BaseModel):
    """Corpo da requisição de chat."""

    home_team_id: str
    away_team_id: str
    question: str = "Quem tem mais chance de vencer e por quê?"
    response_language: str = "pt-BR"


def _sse(events: Iterator[dict[str, object]]) -> Iterator[str]:
    for event in events:
        yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


@router.post("/stream")
def chat_stream(request: ChatRequest, repo: RepoDep) -> StreamingResponse:
    """Executa a orquestração de LLMs e transmite os eventos por SSE.

    Requer LM Studio com os modelos configurados em `models.yaml`.
    """
    for team_id in (request.home_team_id, request.away_team_id):
        if repo.get_team(team_id) is None:
            raise HTTPException(status_code=404, detail=f"team not found: {team_id}")

    settings = get_settings()
    specs = load_model_specs()
    client = LMStudioClient(
        base_url=settings.lmstudio_base_url,
        api_key=settings.lmstudio_api_key,
        timeout=float(settings.lmstudio_timeout_seconds),
    )
    orchestrator = SequentialOrchestrator(
        client, specs["analyst"], specs["challenger"], specs["auditor"]
    )
    pack = build_evidence_pack(repo, request.home_team_id, request.away_team_id)
    events = orchestrator.run_events(
        request.question, pack, response_language=request.response_language
    )
    return StreamingResponse(_sse(events), media_type="text/event-stream")
