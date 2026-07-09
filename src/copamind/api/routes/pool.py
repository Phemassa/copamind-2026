"""Rotas do Bolao de IAs Locais (E11)."""

from __future__ import annotations

import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated
from urllib.parse import urlparse
from uuid import uuid4

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from copamind.api.dependencies import get_repository
from copamind.data.fifa_stats import team_label as _team_label
from copamind.data.repositories import DuckDBRepository
from copamind.llm.client import LLMError, LMStudioClient, extract_json
from copamind.models.calibration.report import CalibrationReport, calibration_report
from copamind.pool.service import (
    BacktestSummary,
    PredictorStanding,
    leaderboard,
    run_backtest,
)
from copamind.pool.llm_progress import (
    new_llm_batch_id,
    read_latest_llm_phase_progress,
    read_llm_phase_progress,
    write_llm_phase_progress,
)

router = APIRouter(tags=["pool"], prefix="/pool")

RepoDep = Annotated[DuckDBRepository, Depends(get_repository)]


class LLMPhaseRunRequest(BaseModel):
    """Pedido para iniciar o agente das LLMs em uma fase."""

    phase: str = Field(default="round_of_16")
    model_id: str | None = None
    samples: int = Field(default=1, ge=1, le=3)
    include_heavy: bool = True
    finished_only: bool = False


class LLMPhaseRunResponse(BaseModel):
    """Resposta imediata do disparo em background."""

    status: str
    batch_id: str
    command: list[str]


class LLMPhaseProgressResponse(BaseModel):
    """Progresso ao vivo de uma execucao por fase."""

    batch_id: str
    phase: str | None = None
    status: str = "starting"
    current_match_index: int = 0
    total_matches: int = 0
    current_match_label: str | None = None
    current_model_index: int = 0
    total_models: int = 0
    current_model_id: str | None = None
    current_sample_index: int = 0
    total_samples: int = 0
    completed_calls: int = 0
    total_calls: int = 0
    percent: float = 0.0
    elapsed_seconds: float = 0.0
    eta_seconds: float | None = None
    message: str | None = None
    updated_at: str | None = None


class LLMResetRequest(BaseModel):
    """Pedido para limpar historico de chamadas das LLMs."""

    phase: str | None = None
    model_id: str | None = None


class LLMResetResponse(BaseModel):
    """Resumo do reset executado."""

    status: str
    deleted: dict[str, int]


class TeamContextNoteRequest(BaseModel):
    """Nota manual controlada para enriquecer o contexto das LLMs."""

    phase: str
    team_id: str
    match_id: str | None = None
    note_type: str = Field(default="team_news")
    title: str = Field(min_length=3, max_length=120)
    note_text: str = Field(min_length=8, max_length=1200)
    impact: dict[str, object] = Field(default_factory=dict)
    source: str = Field(default="manual")
    source_url: str | None = None
    confidence: float = Field(default=0.75, ge=0.0, le=1.0)
    weight: float = Field(default=0.7, ge=0.0, le=1.0)
    available_at: datetime | None = None


class TeamContextNoteResponse(BaseModel):
    """Nota contextual serializada para portal/API."""

    note_id: str
    phase: str
    team_id: str
    match_id: str | None = None
    note_type: str
    title: str
    note_text: str
    impact: dict[str, object]
    source: str
    source_url: str | None = None
    confidence: float
    weight: float
    available_at: datetime
    created_at: datetime
    active: bool


@router.post("/backtest", response_model=BacktestSummary)
def backtest(repo: RepoDep) -> BacktestSummary:
    """Roda o bolao sobre o historico e retorna a classificacao dos preditores."""
    return run_backtest(repo)


@router.get("/leaderboard", response_model=list[PredictorStanding])
def get_leaderboard(repo: RepoDep) -> list[PredictorStanding]:
    """Retorna a classificacao atual do bolao."""
    return leaderboard(repo)


@router.get("/calibration", response_model=list[CalibrationReport])
def get_calibration(repo: RepoDep) -> list[CalibrationReport]:
    """Relatorio de calibracao por preditor."""
    return calibration_report(repo)


@router.get("/context-notes", response_model=list[TeamContextNoteResponse])
def list_context_notes(
    repo: RepoDep,
    phase: str | None = None,
    team_id: str | None = None,
) -> list[TeamContextNoteResponse]:
    """Lista notas contextuais manuais usadas como evidencia nas chamadas LLM."""
    rows = repo.list_team_context_notes(phase=phase, team_id=team_id, active_only=False)
    repo.close()
    return [TeamContextNoteResponse(**row) for row in rows]


@router.post("/context-notes", response_model=TeamContextNoteResponse)
def create_context_note(
    request: TeamContextNoteRequest,
    repo: RepoDep,
) -> TeamContextNoteResponse:
    """Cria uma nota contextual controlada para a fase/selecao."""
    now = datetime.now(UTC)
    note_id = f"context-note:{uuid4().hex}"
    repo.upsert_team_context_note(
        note_id=note_id,
        phase=request.phase,
        team_id=request.team_id,
        match_id=request.match_id,
        note_type=request.note_type,
        title=request.title,
        note_text=request.note_text,
        impact=request.impact,
        source=request.source,
        source_url=request.source_url,
        confidence=request.confidence,
        weight=request.weight,
        available_at=request.available_at or now,
        created_at=now,
        active=True,
    )
    row = next(
        item for item in repo.list_team_context_notes(active_only=False)
        if item["note_id"] == note_id
    )
    repo.close()
    _export_portal()
    return TeamContextNoteResponse(**row)


@router.delete("/context-notes/{note_id}", response_model=dict[str, str])
def deactivate_context_note(note_id: str, repo: RepoDep) -> dict[str, str]:
    """Desativa uma nota contextual sem apagar a auditoria."""
    ok = repo.deactivate_team_context_note(note_id)
    repo.close()
    _export_portal()
    return {"status": "inactive" if ok else "not_found", "note_id": note_id}


# ── Extrator de noticias via LLM ──────────────────────────────────────────────

_PHASE_LABELS: dict[str, str] = {
    "group_stage": "Fase de grupos",
    "round_of_32": "32 avos de final",
    "round_of_16": "Oitavas de final",
    "quarterfinal": "Quartas de final",
    "semifinal": "Semifinal",
    "third_place": "Disputa de 3o lugar",
    "final": "Final",
}

_VALID_NOTE_TYPES = {"team_news", "rotation", "injury", "tactical", "morale", "travel"}
_VALID_IMPACTS = {
    "recent_form_downweight",
    "physical_load_positive",
    "injury_negative",
    "tactical_positive",
    "volatility_up",
}


class ContextNoteExtractRequest(BaseModel):
    """Pedido de extracao de nota contextual a partir de uma URL."""

    url: str = Field(min_length=10)
    phase: str
    team_id: str


class ContextNoteExtractResponse(BaseModel):
    """Nota contextual pre-preenchida pela LLM para revisao no portal."""

    note_type: str
    title: str
    note_text: str
    impact_key: str
    confidence: float
    weight: float
    available_at: str | None = None
    source: str
    source_url: str


def _strip_html(html: str) -> str:
    """Remove tags HTML e normaliza espacos."""
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s{2,}", " ", text).strip()


def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc or url
    except Exception:
        return url


@router.post("/context-notes/extract", response_model=ContextNoteExtractResponse)
def extract_context_note(request: ContextNoteExtractRequest) -> ContextNoteExtractResponse:
    """Busca uma URL, passa o conteudo a um LLM local e retorna nota pre-preenchida."""
    # 1. Fetch URL
    try:
        resp = httpx.get(
            request.url,
            timeout=12.0,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 CopaMind/2026"},
        )
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Erro ao buscar URL: {exc}") from exc

    excerpt = _strip_html(resp.text)[:4000]

    # 2. Get active model from LM Studio
    llm = LMStudioClient()
    try:
        models = llm.list_models()
    except LLMError as exc:
        raise HTTPException(status_code=503, detail=f"LM Studio indisponivel: {exc}") from exc
    if not models:
        raise HTTPException(status_code=503, detail="Nenhum modelo carregado no LM Studio.")
    model_id = models[0]

    # 3. Build extraction prompt
    team_name = _team_label(request.team_id)
    phase_label = _PHASE_LABELS.get(request.phase, request.phase)
    prompt = (
        "Você é um extrator de contexto esportivo para o CopaMind 2026.\n"
        "Analise o trecho de notícia e extraia informações sobre a seleção indicada.\n\n"
        f"Seleção alvo: {team_name} ({request.team_id})\n"
        f"Fase do torneio: {phase_label}\n"
        f"Fonte: {request.url}\n\n"
        "Trecho da notícia:\n---\n"
        f"{excerpt}\n"
        "---\n\n"
        "Responda SOMENTE com JSON válido, sem texto adicional:\n"
        '{\n'
        '  "note_type": "<team_news|rotation|injury|tactical|morale|travel>",\n'
        '  "title": "<título máx 120 chars>",\n'
        '  "note_text": "<análise analítica do impacto no desempenho, máx 600 chars>",\n'
        '  "impact_key": "<recent_form_downweight|physical_load_positive|injury_negative|tactical_positive|volatility_up>",\n'
        '  "confidence": <0.0-1.0>,\n'
        '  "weight": <0.0-1.0>,\n'
        '  "available_at": "<ISO 8601 da publicação ou null>"\n'
        "}"
    )

    # 4. Call LLM
    try:
        llm_resp = llm.complete(
            model_id=model_id,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        data = extract_json(llm_resp.content)
    except (LLMError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=f"LLM nao retornou JSON valido: {exc}") from exc

    # 5. Sanitize and return
    note_type = str(data.get("note_type", "team_news"))
    if note_type not in _VALID_NOTE_TYPES:
        note_type = "team_news"
    impact_key = str(data.get("impact_key", "recent_form_downweight"))
    if impact_key not in _VALID_IMPACTS:
        impact_key = "recent_form_downweight"
    available_at_raw = data.get("available_at")
    available_at = str(available_at_raw) if available_at_raw and str(available_at_raw) != "null" else None

    return ContextNoteExtractResponse(
        note_type=note_type,
        title=str(data.get("title", ""))[:120],
        note_text=str(data.get("note_text", ""))[:600],
        impact_key=impact_key,
        confidence=max(0.0, min(1.0, float(data.get("confidence", 0.8)))),
        weight=max(0.0, min(1.0, float(data.get("weight", 0.75)))),
        available_at=available_at,
        source=_domain(request.url),
        source_url=request.url,
    )



@router.post("/llm/phase/run", response_model=LLMPhaseRunResponse)
def run_llm_phase(
    request: LLMPhaseRunRequest,
    background_tasks: BackgroundTasks,
) -> LLMPhaseRunResponse:
    """Dispara o agente das LLMs para uma fase/modelo usando o runner CLI."""
    batch_id = new_llm_batch_id()
    write_llm_phase_progress(
        batch_id,
        phase=request.phase,
        status="starting",
        total_samples=request.samples,
        message="Aguardando runner das LLMs iniciar.",
        percent=0.0,
        completed_calls=0,
        total_calls=0,
    )
    command = [
        sys.executable,
        str(Path("scripts/run_llm_phase_benchmark.py")),
        "--phase",
        request.phase,
        "--batch-id",
        batch_id,
        "--samples",
        str(request.samples),
    ]
    if request.model_id:
        command.extend(["--model", request.model_id])
    if not request.include_heavy:
        command.append("--exclude-heavy")
    if request.finished_only:
        command.append("--finished-only")
    background_tasks.add_task(_spawn_runner, command)
    return LLMPhaseRunResponse(status="started", batch_id=batch_id, command=command)


@router.get("/llm/phase/progress", response_model=LLMPhaseProgressResponse)
def get_llm_phase_progress(
    batch_id: Annotated[str, Query(min_length=1)],
) -> LLMPhaseProgressResponse:
    """Retorna o progresso de um batch LLM disparado pelo portal."""
    progress = read_llm_phase_progress(batch_id) or {
        "batch_id": batch_id,
        "status": "starting",
        "message": "Aguardando runner das LLMs iniciar.",
    }
    return LLMPhaseProgressResponse(**progress)


@router.get("/llm/phase/progress/latest", response_model=LLMPhaseProgressResponse)
def get_latest_llm_phase_progress(
    phase: str | None = None,
) -> LLMPhaseProgressResponse:
    """Retorna o batch de progresso mais recente para recuperar a tela apos reload."""
    progress = read_latest_llm_phase_progress(phase) or {
        "batch_id": "",
        "phase": phase,
        "status": "idle",
        "message": "Nenhum batch recente encontrado.",
    }
    return LLMPhaseProgressResponse(**progress)


@router.post("/llm/reset", response_model=LLMResetResponse)
def reset_llm_history(
    request: LLMResetRequest,
    repo: RepoDep,
) -> LLMResetResponse:
    """Limpa historico de chamadas/palpites das LLMs."""
    deleted = repo.reset_llm_history(phase=request.phase, model_id=request.model_id)
    repo.close()
    _export_portal()
    return LLMResetResponse(status="reset", deleted=deleted)


def _spawn_runner(command: list[str]) -> None:
    subprocess.Popen(command, cwd=Path.cwd())


def _export_portal() -> None:
    subprocess.run(
        [sys.executable, str(Path("scripts/export_portal_data.py"))],
        cwd=Path.cwd(),
        check=False,
    )
